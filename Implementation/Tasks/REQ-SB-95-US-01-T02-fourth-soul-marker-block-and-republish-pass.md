---
id: REQ-SB-95-US-01-T02
title: The fourth SOUL.md marker block (## Who you work for) and the one-pass, one-reload republish
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (scope-internal judgement calls, spot-check only — nothing is blocked): five shape decisions inside this task's own files, logged in full in the Implementation Log — (1) the published own address is labelled with the setting it was read from rather than listed as a Profile fact; (2) the pass writes Hermes' SOUL.md and NOT the Registry's own `Agent.json`/`soul.md` mirror, which `update()` would have written; (3) the single Registry reload is at the end of the pass and is honestly described as a cost cap rather than as load-bearing; (4) `_OPERATOR_PROFILE_EDITED_AT` lives in `agent_manager.py` because its natural home, `operator_profile.py`, is another task's file; (5) the block is published to an unconfigured install carrying the own address, which comes from a configured setting. PLUS the two manual steps in `## Tests` were performed on a disposable install up to — and NOT including — their 'ask a real agent in a real chat' half, which would require publishing the operator's real name and team into the real install's 43 profiles and a real model call; both ACs are verified by their AC-tagged automated steps. Disclosed in REVIEW-QUEUE.md. No ESCALATIONS entry, no ADR touched, no new dependency, no file outside the list."
phase: P2
depends_on: [REQ-SB-95-US-01-T01]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-01-T02 — The Fourth Marker Block + The Republish Pass

## Parent Story

- Story: [[REQ-SB-95-US-01]] — `../UserStories/REQ-SB-95-US-01-operator-profile.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Publish the operator's facts into every agent's context as a fourth
auto-generated, marker-delimited SOUL.md block headed `## Who you work for`,
written by **one** republish pass that reloads the Registry exactly once and is
triggered by the Profile save.

---

## Starting State → End State

**Before / Inputs:**

- `app/business/core/agents/agent_manager.py` already owns two auto-generated
  blocks with exactly the idempotent replace-own-block shape to copy (read
  directly): `_SPECIALISTS_BEGIN`/`_SPECIALISTS_END` and
  `_INDEX_GUIDANCE_BEGIN`/`_INDEX_GUIDANCE_END`, each found via
  `prompt.find(BEGIN)`/`find(END)` and replaced in place by
  `_apply_specialists_block` / `_apply_index_guidance_block`.
- **SOUL.md is the store, not a render target.** `_to_agent()` reads the real
  soul back through `_split_soul_sections()`, and that is where `Agent.prompt`
  comes from — so a block composed in `_soul_text()` with no inverse on read is
  absorbed into the prompt and becomes hand-editable (`ADR-036`).
- `_split_soul_sections()` matches the exact headings `## Guardrails` and
  `## Scope` **anywhere** in the text and cuts their bodies into other fields.
- `AgentManager.update()` calls `_reload_registry()`, which is
  `asyncio.run(registry_loader.boot())` — a full Registry boot **per call**
  (41 of them on the reporting install).
- `SkillManager` calling `publish_section_access_map()` on every
  deploy/undeploy is the derived-republish *trigger* precedent.

**After / Outputs:**

- A fourth marker pair in `AgentManager` and a generator that composes ONE
  block of text from the Operator Profile: the operator's name, their own
  address (**mirrored from the `SELF_EMAIL` setting**, `ADR-038`), their other
  addresses, and each team member with their role. Identical text in every
  agent — a singleton fans out, it does not recompute per agent.
- Heading `## Who you work for` — never `## Guardrails`, never `## Scope`.
- The block is **present even when the Profile is unconfigured**, saying so and
  naming where to configure it. It is never removed when empty (this is the
  deliberate difference from the two precedents, and it is what makes AC-05
  answerable at all).
- **One republish pass**: a dedicated `AgentManager` method that walks every
  agent once, writes each agent's soul, and reloads the Registry **exactly
  once** for the whole pass. It does **not** call `update()` per agent.
- `OperatorProfileManager.save()` triggers that pass. Editing the Profile is
  the only action a human takes.

---

## Files to Modify

- `src/backend/app/business/core/agents/agent_manager.py`
- `src/backend/app/business/core/operator/operator_profile_manager.py` (the republish trigger)
- `src/backend/tests/test_operator_profile_publication.py` (new)

---

## Constraints

- Inherits from parent story.
- **Derived, never hand-copied.** No agent's stored prompt text may be mutated
  to carry a hand-written copy of the operator's facts.
- **Not `## Guardrails` / `## Scope`** — those exact headings are claimed by
  `_split_soul_sections()` and would mis-parse the block's body into the wrong
  field (a real 2026-08-28 defect, recorded in that function's own docstring).
- **Not a compose-time injection into `_soul_text()` without an inverse** — see
  Starting State; this must be a marker block that already round-trips.
- **No second published file.** Do not write an `operator_profile.json` beside
  `section_access.json`, and do not touch `section_access.json` (`ADR-036`
  rejected that explicitly).
- **One Registry reload per pass, not per agent.** This is a locked AC, not a
  performance preference.
- The own address is **read** from the `SELF_EMAIL` setting at publish time and
  never written back anywhere.
- Existing agent behaviour is otherwise unchanged — specialists block, index
  guidance block, prompt/guardrails/scope round-trip, ordinary chat.
- `REQ-SB-95-US-03-T01` adds a *third* block (the Action catalogue) to this same
  file and, per `architecture.md`, **reuses this republish seam unchanged**.
  Build the pass so a second caller can use it; do not edit the `US-03` task
  files (they are another story's and already `Ready`) — note the overlap in
  the Implementation Log if the two land out of order.

---

## Tests

**Automated tests** — `src/backend/tests/test_operator_profile_publication.py`,
run with `pytest tests/test_operator_profile_publication.py` from
`src/backend`; follow `tests/test_soul_and_profile_hygiene.py`'s existing
technique for exercising real SOUL text.

1. `[REQ-SB-95-US-01-AC-02]` With a Profile holding a name and three colleagues
   with roles, run the republish across three fake agents; assert each agent's
   soul contains exactly one `## Who you work for` block between its own
   markers, that the block names the operator and all three colleagues with
   their roles, and that the three agents' block texts are **byte-identical**
   to each other.
2. `[REQ-SB-95-US-01-AC-02]` Assert the generated heading is `## Who you work
   for` and that neither `## Guardrails` nor `## Scope` appears inside the
   block; then round-trip the composed soul through `_split_soul_sections()`
   and assert `guardrails` and `scope` are unchanged by its presence.
3. `[REQ-SB-95-US-01-AC-02]` Republish twice with a changed Profile; assert
   exactly one marker pair exists, the content reflects the change, and every
   character outside the markers is byte-identical to before.
4. `[REQ-SB-95-US-01-AC-02]` Assert `OperatorProfileManager.save()` triggers
   the republish (spy on the pass) — no caller has to remember to — and that
   no agent's hand-authored prompt text was edited by hand anywhere in the run.
5. `[REQ-SB-95-US-01-AC-04]` With `settings.self_email` monkeypatched, assert
   the published block carries that address; change the setting, republish, and
   assert the block carries the new one — with nothing written back to the
   setting, to `.env`, or to `Profile.json`.
6. `[REQ-SB-95-US-01-AC-05]` With **no** Profile saved, run the republish;
   assert the block is still present in every agent, that its text states no
   Operator Profile is configured and names where to configure it, and that it
   invents no team.
7. `[REQ-SB-95-US-01-AC-07]` Spy on `registry_loader.boot` (and on
   `AgentManager.update`) across a republish over N≥3 agents; assert `boot` was
   awaited **exactly once** for the whole pass and `update` was called **zero**
   times, while each agent's soul was written once.

**Manual verification steps:**

1. `[REQ-SB-95-US-01-AC-02]` With the backend running and a real Profile saved,
   open a real chat with an agent and ask who your team is; confirm it names
   exactly the recorded colleagues and no one else, and record the reply
   verbatim in the Implementation Log.
2. `[REQ-SB-95-US-01-AC-05]` Move the real `Profile.json` aside, republish, ask
   the same question, and confirm the agent says plainly that no Operator
   Profile is configured rather than guessing a team from mail traffic or vault
   notes. Restore the file afterwards.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Fourth marker-delimited auto-generated block, same shape as the existing two
- [x] Heading `## Who you work for`; `_split_soul_sections()` round-trip unaffected
- [x] Identical text fanned out to every agent; idempotent re-publish
- [x] Block present and honest when the Profile is unconfigured
- [x] One pass, one Registry reload, zero per-agent `update()` calls
- [x] Triggered by the Profile save, no hand-edited prompt
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **not appended.** `MEMORY.md` stands at 86 KB against the 40 KB budget its
      own rule 1 sets, which forbids appending while over. This is the fifth task
      in three days to be stopped by it. Two candidates are written out in
      `REVIEW-QUEUE.md` for the compaction pass.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Action catalogue block — `REQ-SB-95-US-03-T01`.
- Export behaviour of the published text — `T04` (and the open privacy question
  behind it, which this task must not pre-empt in either direction).
- Any screen — `T05`.
- Making a running Hermes gateway re-read a soul it has already loaded —
  `ADR-035`/`ADR-036` accept that limitation explicitly; do not engineer around it.

---

## Context / Notes

`architecture.md` → **§Operator Facts in Agent Context — the Fourth Marker
Block** and `ADR-036` are authoritative; `ADR-038` changes only *where the
operator's own address comes from* (the setting), not how publication works.

Read the real current `agent_manager.py` marker handling before editing — this
project's Learnings repeatedly record that a task's illustrative shape must be
composed around the real current file, and `agent_manager.py` is actively
extended by sibling `REQ-SB-95` stories.

---

## Implementation Log

**2026-10-18 — built and verified. `status: Done`, `gate: flagged` (trigger-1
only — a spot-check; nothing is blocked and `T04` is unblocked).** All four
locked ACs (`AC-02`, `AC-04`, `AC-05`, `AC-07`) verified in automated mode, on
14 AC-tagged tests plus a byte-for-byte proof on a real SOUL.md in a scratch
Hermes home.

### What was built — three files, nothing else touched

| File | What changed |
|---|---|
| `app/business/core/agents/agent_manager.py` | the marker pair, the block generator, the idempotent apply, and `publish_operator_profile()` — the one-pass/one-reload/no-`update()` walk |
| `app/business/core/operator/operator_profile_manager.py` | the republish trigger: `publish_operator_profile()` / `_publish_into()` / `publish_operator_profile_in_background()` / `join_background_publications()`, fired by `save()` |
| `tests/test_operator_profile_publication.py` | new — 14 tests, all AC-tagged |

- **The block.** `<!-- BEGIN OPERATOR PROFILE … -->` / `<!-- END OPERATOR
  PROFILE -->`, heading `## Who you work for`, beside the specialists,
  index-guidance, Action and Workflow blocks — so it is in fact the **fifth**
  marker pair, not the fourth this task's title names. `SPRINT-086`'s own
  Dependencies note anticipated exactly this ("the ordinal is cosmetic naming;
  no AC and no behaviour depends on it") because `US-03-T01` and `US-04-T06`
  landed theirs first; the title is left as written (specs are append-only).
  Sub-headings are `###` so nothing
  inside it can collide with the exact `## Guardrails`/`## Scope` headings
  `_split_soul_sections()` matches anywhere in the text. It names the operator,
  their own address, their other addresses, their timezone and each colleague
  as `` `email` -- role ``, and it closes by telling the agent to name exactly
  those people and to say so rather than assembling a team from mail traffic or
  vault notes.
- **It fans out rather than recomputing.** The Profile is a singleton, so the
  block text is composed ONCE per pass from one `OperatorProfileManager.get()`
  and the same characters are applied to every agent. The Action and Workflow
  blocks are filtered per agent by what that agent may call; an operator is not,
  and the four agents' block texts are asserted byte-identical to one another.
- **It is never removed when empty.** An unconfigured Profile publishes the
  block saying `**No Operator Profile is configured on this install.**`, naming
  `Settings > Operator Profile`, and telling the agent not to assemble a team.
- **The pass.** `publish_operator_profile()` takes `_publication_lock`, reads the
  roster, returns `[]` at once if it is empty, reads the Profile, writes each
  agent's real SOUL.md through `HermesProfiles.write_soul` and reloads the
  Registry exactly once at the end — `update()` is never called.
- **The trigger.** `OperatorProfileManager.save()` fires
  `publish_operator_profile_in_background()` after the write, copying
  `WorkflowManager`'s shape exactly, so editing the Profile is the whole
  operation and the `T03` router gets publication for free without firing it a
  second time. The pass binds itself to **both** halves of the install it was
  started for (`hermes_home_path` **and** `second_brain_data_path`) and abandons
  itself if either is reconfigured under it.

### Verification — automated mode, `pytest` from `src/backend`

`.venv/Scripts/python.exe -m pytest tests/test_operator_profile_publication.py -q`
→ **14 passed in 2.97s**.

- **Suite baseline measured on the tree this task started from** (whole suite,
  this file excluded): **696 passed, 0 failed, 39.34s**. After: **710 passed, 0
  failed, 41.52s** — +14, all mine, nothing else moved. (The recorded
  686 has since grown by 10 from other sessions' tests; 696 is this tree's real
  baseline, measured rather than carried forward — `ef19334`.) None of the four known
  order-dependent tests failed in either full run.
- **Every test runs against a real scratch Hermes home with four real profiles
  on disk** under `tmp_path`, through the real `HermesProfiles.read_soul`/
  `write_soul` — not a dict standing in for Hermes. `BUG-092`/`BUG-093` were
  both in this write path and reasoning about `_rewrite_soul()` is not proof.
- **The operator's real install was never touched, and that is measured, not
  assumed.** `tests/conftest.py` sandboxes Hermes suite-wide; this file then
  points `hermes_home_path` and `second_brain_data_path` at `tmp_path` and
  restores the Registry's module-level globals. Checked afterwards against the
  real install: `<DATA_PATH>/data/Operator` **does not exist**, and **0 of the
  43 `SOUL.md` files** under the real Hermes home have an mtime inside the last
  two hours. Every value in the tests and in the scratch run is fictitious
  (`Robin Fictional`, `operator@example.test`, `blue/green/amber@example.test`).

### Each locked AC, with what was observed

**`REQ-SB-95-US-01-AC-02` — one derived, marker-delimited block, identical in
every agent, replacing its own prior copy. PASS.** Six tagged tests.

- `test_the_operator_and_the_whole_team_reach_every_agent_identically` — a
  Profile with a name, two other addresses, a timezone and three colleagues
  with roles, published across four agents. Observed: all four republished;
  exactly one `BEGIN`/`END` pair in each; the four block texts reduce to a set
  of size **1**; the block names `Robin Fictional`, each of the three
  colleagues as `` `email` -- role ``, both other addresses and the timezone.
- `test_the_heading_is_who_you_work_for_and_the_soul_still_splits_the_same` —
  observed `\n## Who you work for\n` inside the block, `## Guardrails` and
  `## Scope` both **absent** from it, and the composed soul round-tripped
  through the real `_split_soul_sections()`: `guardrails` is still
  `"Never invent a number."` and `scope` is still
  `{"folders": ["Customers"], "tags": ["adnoc"]}` — identical to before
  publication. The block comes back inside the **core prompt**, which is where
  a marker block belongs.
- `test_republishing_a_changed_profile_replaces_its_own_block_and_nothing_else`
  — published, renamed the operator, replaced the whole team, republished.
  Observed: one marker pair still; `Robin Renamed` and
  `` `violet@example.test` -- Chief of Staff `` present; `Robin Fictional` and
  the removed colleague **absent from the whole file**; every character outside
  the markers byte-identical.
- `test_publishing_into_a_real_profile_changes_only_the_block` — the byte
  contract, on a real file. See the measured numbers below.
- `test_saving_the_profile_is_the_only_action_anyone_takes` — a plain `save()`,
  then the real background thread joined. Observed: the block arrived in all
  four real SOUL.md files, and `soul.count("Robin Fictional") == 1` in every
  one of them — the operator's name exists only inside the derived block, so
  nothing hand-copied it into an agent's own prompt text. The hand-authored
  file reduces to itself exactly: `soul.replace("\n\n" + block, "") ==
  HAND_AUTHORED_SOUL`.
- `test_the_save_returns_before_the_publication_finishes` and
  `test_a_pass_that_outlives_its_install_publishes_into_nothing` — the save
  returns with its record while the pass it started is still blocked inside its
  own run; a pass started for one install refuses to publish after **either**
  `hermes_home_path` or `second_brain_data_path` changes, and still publishes
  into the one it was started for.
- `test_an_action_pass_and_an_operator_pass_never_drop_each_others_block` — the
  lost-update guard. The Operator pass is held open inside its first write and
  an Action pass is started on top of it; both blocks survive in all four
  profiles. **Confirmed to FAIL with the lock replaced by a `nullcontext`**
  (run with a one-off pytest plugin patching
  `agent_manager._publication_lock`): `AssertionError: blue-agent` — the Action
  pass had written the file back without the Operator block, leaving
  `<!-- BEGIN ACTION CATALOGUE … -->` and nothing of this task's. The guard is
  real, not decorative.

**`REQ-SB-95-US-01-AC-04` — the own address is published from the setting, and
written nowhere. PASS.** Two tagged tests.

- `test_the_block_says_where_the_own_address_came_from_and_tracks_the_setting`
  — observed the address in the block carrying `` `SELF_EMAIL` ``,
  `Settings > System` and the words `not from the Operator Profile`; then the
  setting was repointed and the next pass republished **every** agent with the
  new address and no trace of the old one anywhere in the file. The written
  `Profile.json` was read back as **bytes**: neither address appears in them,
  nor the keys `self_email`/`own_address`; `settings.self_email` is unchanged by
  publication; and no `.env` exists anywhere under either scratch root.
- `test_saving_the_profile_never_touches_the_self_email_setting` — a spy on
  `setup_wizard.sync_settings_to_hermes` recorded **zero** calls across a save
  and a publication, and because a module-attribute spy cannot see a
  `from … import` binding, the absence of any `setup_wizard` import is pinned on
  both modules' source.

**`REQ-SB-95-US-01-AC-05` — an unconfigured Profile is answered honestly. PASS.**
Two tagged tests.

- `test_an_unconfigured_profile_is_published_as_unconfigured` — with no Profile
  ever saved, observed the block present in **all four** agents, stating
  `No Operator Profile is configured on this install.`, naming
  `Settings > Operator Profile`, and telling the agent `do not assemble one`
  from mail traffic or vault notes. It invents nobody: `Robin`,
  `blue@example.test`, `Engineer` and `@example.invalid` are all absent.
- `test_an_unconfigured_install_with_no_self_email_says_that_too` — the emptiest
  install there is. Observed `Their own mail address: not configured`, with the
  setting named, rather than a blank value printed as if it were one.

**`REQ-SB-95-US-01-AC-07` — one pass, one Registry reload, zero `update()`
calls. PASS.** Two tagged tests.

- `test_one_pass_reloads_the_registry_once_and_never_calls_update` — four agents
  (N≥3 asserted in the test itself). Observed: `registry_loader.boot` awaited
  **exactly once** for the whole pass, `AgentManager.update` called **zero**
  times, and each of the four agents' souls written **exactly once** (counted at
  the real `HermesProfiles.write_soul`).
- `test_a_pass_with_nothing_to_change_writes_nothing_and_reloads_nothing` — a
  second pass over an unchanged Profile returns `[]`, writes **no** soul and
  boots the Registry **zero** times.

### Byte-for-byte proof, on a real file, measured not argued

A scratch Hermes home with a real SOUL.md carrying prose this app cannot read
(`## Scope boundary`, prose inside `## Scope`, a final newline), published into
by a real `OperatorProfileManager.save()` through its own real background
thread:

```
before : 190 bytes      after : 1619 bytes      block : 1427 bytes (+2 for the blank line)
after.replace(b"\n\n" + block, b"") == before : True
CRLF introduced : False      final newline kept : True      marker pairs : 1
second pass : []  -> file bytes identical AND st_mtime_ns identical
```

The same assertion is pinned in
`test_publishing_into_a_real_profile_changes_only_the_block`.

### The two manual steps — what was performed, and what was not

Both manual steps end in "ask a real agent in a real chat". Performing that half
as written would mean publishing the operator's **real** name and **real
colleagues** into the real install's 43 profiles and spending a real model call,
which this task's standing conditions forbid outright. The rest of both steps
was performed on a **disposable** install (scratch `HERMES_HOME_PATH` and
`SECOND_BRAIN_DATA_PATH`), reading back what the agent is really given through
`HermesProfiles.read_soul_document()` — `ADR-043`'s "the text as written",
nothing excerpted or reassembled.

1. `[REQ-SB-95-US-01-AC-02]` **Performed up to the chat.** A real Profile saved
   over the real Manager; the block arrived in the real profile's SOUL.md on the
   save alone, verbatim as printed above: the three team lines are exactly the
   recorded colleagues and no one else, and the text instructs the agent to name
   exactly those people. **Not performed:** the live reply from a model.
2. `[REQ-SB-95-US-01-AC-05]` **Performed up to the chat.** `Profile.json` moved
   aside on the disposable install and the pass re-run: the configured block was
   replaced **in place** (one marker pair, `## Guardrails`/`## Scope` and the
   final newline untouched) by the unconfigured one, verbatim:

   ```
   **No Operator Profile is configured on this install.** It is recorded on
   Settings > Operator Profile, and until it is you do not know the operator's
   name, their other mail addresses, their timezone, or who is on their team.

   Asked any of that, say exactly that -- that this install has no Operator
   Profile configured and that it is set on Settings > Operator Profile. Do not
   name a team, and do not assemble one from mail traffic, vault notes or
   anything else.
   ```

   Re-running the pass with the file still aside republished **nothing** (`[]`,
   idempotent); restoring the file and re-running republished both agents and
   the team was named again. **Not performed:** the live reply from a model.

This is disclosed in `REVIEW-QUEUE.md` rather than treated as a block: both ACs
carry AC-tagged **automated** steps in this task's own `## Tests`, all of which
pass, and `Pipeline.md`'s manual → automated upgrade makes those the primary
verification now that the stack runs.

### Scope-internal judgement calls (the gate flag — spot-check, nothing blocked)

1. **The published own address is labelled with the setting it came from.**
   `AC-04` requires it published; it does not require it published as a Profile
   fact. It reads `-- read from this app's own \`SELF_EMAIL\` setting, edited on
   Settings > System, not from the Operator Profile, which does not store it`,
   built from the `setting_key`/`edited_at` the `MirroredOwnAddress` value
   already carries rather than from a second hardcoded copy. Listing it
   unattributed beside the Profile's own fields would be true about the operator
   and false about the record it appears to come from — and the first person to
   go looking for it on the Operator Profile page would not find it there.
   Consequently, on an **unconfigured** install the block still publishes the
   address (it comes from a configured setting) while stating plainly that no
   Profile is configured; both halves are true of different stores.
2. **The pass writes Hermes' SOUL.md and NOT the Registry's own mirror.**
   `update()` also pushes `Agent.json`/`soul.md` into the Registry tree, and
   bypassing `update()` (which `AC-07` requires) means that mirror is not
   refreshed by this pass. Taken deliberately: the Registry's `soul.md` is
   loaded into `Agent.soul`, which **nothing reads** (grepped), and the loader is
   fail-loud only on a *missing* one, which publication never causes — whereas
   writing it from here would mean rebuilding the whole `Agent.json` config from
   a roster read, and `get_all()` is deliberately cheap
   (`include_skills=False`), so every agent's `skill_ids` would be mirrored back
   as `[]`. A stale mirror nobody reads is much smaller than a Registry that
   forgets which Skills an agent declares. A side effect worth naming: it also
   means this pass never reaches `registry_writer.agent_dir()`, the pre-existing
   `TypeError` for a `section_id is None` agent that `REQ-SB-95-US-04-T06`
   reported — this pass cannot hit it, and it reports an agent as republished
   only when `write_soul` really returned.
3. **The one Registry reload is at the end, and is described honestly.** `AC-07`
   locks "exactly ONCE for the whole pass", and that is what the code does. But
   since the pass writes no Registry file, the reload refreshes nothing this
   pass changed: it is a cost cap (one boot where `update()` would have run 41),
   not a correctness step, and the code comment says exactly that rather than
   implying otherwise. A pass that changed nothing reloads nothing, because it
   wrote nothing to refresh — pinned by its own test.
4. **`_OPERATOR_PROFILE_EDITED_AT = "Settings > Operator Profile"` lives in
   `agent_manager.py`.** Its natural home is beside `OWN_ADDRESS_EDITED_AT` in
   `operator_profile.py`, which is `T01`'s file and not in this task's `## Files
   to Modify`. Reaching into it for one constant is exactly the out-of-scope
   edit this project blocked four tasks on today, so the constant is defined
   here with a comment naming where it belongs. Worth a one-line move whenever
   that file is next legitimately open.
5. **`save()` publishes on a background thread and does not wait.** The task
   says only "triggers that pass". Blocking would make one `PUT
   /operator/profile` hold the screen for a roster-wide rewrite — the same
   measured reason behind the operator's 2026-10-18 decision for the Action
   catalogue — so this copies `WorkflowManager`'s shape exactly, including
   `join_background_publications()` for callers that need the roster to have
   settled. Accepted consequence: for a few seconds after a save an agent's
   block may still name the old team.

### Note for `REQ-SB-95-US-03` and `T04`

- `US-03`'s Action catalogue already has its own publication seam
  (`publish_action_catalogue`), built by `REQ-SB-95-US-03-T01` before this task
  landed, so the two stories' passes are siblings rather than one reused method.
  Both now take `_publication_lock`, which is what keeps them from dropping each
  other's block. The lighter walk built here (no `update()`, one reload) is the
  shape that pass could adopt later; that is a change to `US-03`'s own code and
  is not made here.
- `T04` (export) should know the published text now carries colleague names and
  addresses in every profile's SOUL.md — that is `AC-08`'s open privacy question
  and this task deliberately does not pre-empt it in either direction.

gate: flagged 2026-10-18 — trigger 1 (the five judgement calls above) plus the
disclosed manual-step limit. Trigger 6 does not apply: every locked AC is
verified. No `ESCALATIONS.md` entry: nothing outside this task's `## Files to
Modify` was changed, and the one place that would have forced it (the constant
in `operator_profile.py`) was avoided rather than reached.
