---
id: REQ-SB-95-US-01-T02
title: The fourth SOUL.md marker block (## Who you work for) and the one-pass, one-reload republish
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-01-T01]
created: 2026-10-16
updated: 2026-10-16
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

- [ ] Fourth marker-delimited auto-generated block, same shape as the existing two
- [ ] Heading `## Who you work for`; `_split_soul_sections()` round-trip unaffected
- [ ] Identical text fanned out to every agent; idempotent re-publish
- [ ] Block present and honest when the Profile is unconfigured
- [ ] One pass, one Registry reload, zero per-agent `update()` calls
- [ ] Triggered by the Profile save, no hand-edited prompt
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

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

_(Filled in by the coder.)_
