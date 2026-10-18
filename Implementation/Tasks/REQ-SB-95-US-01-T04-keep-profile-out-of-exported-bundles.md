---
id: REQ-SB-95-US-01-T04
title: Keep the Operator Profile out of an exported bundle, and disclose what a real Agent bundle still carries
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "coder scope-internal judgement calls, for human spot-check (not blockers): (1) the two MANUAL steps were performed against a real `.sbf` built from a SCRATCH store, not the operator's real one — this session is standing-ordered never to build a bundle from the real store; (2) `_export_agent_profile_tarball` is monkeypatched to inert bytes in the guard, because the suite sandboxes Hermes and `ADR-014` makes that tarball opaque; (3) the AC-08 disclosure for `profile.tar.gz` is therefore reported from the code path, not from a real tarball's contents. Also carries the `MEMORY.md` over-budget item — see `REVIEW-QUEUE.md`."
phase: P2
depends_on: [REQ-SB-95-US-01-T01, REQ-SB-95-US-01-T02]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-01-T04 — The Profile Does Not Travel

## Parent Story

- Story: [[REQ-SB-95-US-01]] — `../UserStories/REQ-SB-95-US-01-operator-profile.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make "the Operator Profile is excluded from artifact export" (`ADR-032`) a
proven, guarded property rather than an accident of it not being a kind yet —
**and**, separately and without changing any behaviour, record exactly what a
real exported Agent bundle contains today, so the operator can settle the open
privacy question on facts.

---

## Starting State → End State

**Before / Inputs:**

- `business/logic/artifacts_inventory.py` enumerates the artifact kinds;
  `artifact_dependency_resolver.py` builds a closure; `artifact_export.py`
  writes the payload per kind via `_PAYLOAD_FOLDER`; `artifact_seed_data.py`
  adds allowlisted, **plugin-registered** seed-data paths as empty files.
- The Operator Profile is not an artifact kind and nothing registers it as
  seed data — true today, and nothing currently stops a future change from
  sweeping `data/Operator/` in alongside `data/Actions/` and `data/Workflows/`.
- `ActionCalls/` and `WorkflowRuns/` are excluded for the same reason
  (`ADR-032`) — instance data, not capability.
- **Confirmed by direct reading, and load-bearing for the disclosure below:**
  `artifact_export.py` copies an exported Agent's registry-side `soul.md`
  verbatim (`content[f"agents/{id}/soul.md"] = soul_path.read_text(...)`) *and*
  writes `agents/<id>/profile.tar.gz`, the raw unmodified output of
  `HermesCLI.export_profile` — which `ADR-014` fixes as an **opaque-bytes**
  boundary and which carries the profile's own SOUL.md.

**After / Outputs:**

- A guard that fails loudly if the Operator Profile ever becomes exportable:
  no `operator`/`profile` artifact kind in the inventory, no `Operator/` path
  in any export payload, no closure entry for it, and no seed-data allowlist
  entry naming `Profile.json`.
- A **disclosure**, not a behaviour change: a real export of a real Agent is
  performed and the Implementation Log records, honestly, whether any Profile
  colleague name or address appears (a) in `agents/<id>/soul.md` and (b)
  inside `agents/<id>/profile.tar.gz`.

---

## Files to Modify

- `src/backend/tests/test_operator_profile_not_exported.py` (new — the guard)
- `src/backend/app/business/logic/artifact_export.py` — **only** if the guard
  finds the Profile genuinely reachable today; if it is already excluded by
  construction, change nothing here and say so in the Implementation Log.

---

## Constraints

- Inherits from parent story.
- **Do not implement either answer to the open privacy question.** Stripping
  the `## Who you work for` block from an exported agent's soul, and accepting
  the leak and documenting it, are both forbidden here. AC-08 is `locked:
  false` precisely because the operator has not chosen yet
  (`REVIEW-QUEUE.md`), and a task that picked one would be the choice.
- **Do not reach inside `profile.tar.gz`.** `ADR-014` makes it opaque bytes;
  this task reads it only to *report* what is in it.
- Minimal change. If AC-06 already holds by construction, the deliverable is
  the guard plus the disclosure — not a refactor of the export machinery.
- Nothing else about exporting may change: the kinds that travel today must
  still travel with byte-identical payloads.

---

## Tests

**Automated tests** — `src/backend/tests/test_operator_profile_not_exported.py`,
run with `pytest tests/test_operator_profile_not_exported.py` from
`src/backend`; follow `tests/test_artifact_seed_data.py` and
`tests/test_blueprint_no_instance_data.py` for the existing
"instance data must not travel" technique.

1. `[REQ-SB-95-US-01-AC-06]` With a real Profile saved under a tmp data path,
   assert `artifacts_inventory` reports no artifact kind for it and that it
   cannot be named in an export selection (the resolver refuses or ignores an
   `operator` kind rather than resolving a closure for it).
2. `[REQ-SB-95-US-01-AC-06]` Build an export payload over a selection covering
   every real kind (including an Agent) and assert no payload key begins with
   `operator`/`Operator`, and that no key anywhere in the payload is
   `Profile.json`.
3. `[REQ-SB-95-US-01-AC-06]` Assert `artifact_seed_data.seed_data_files()`
   contains no entry whose name is `Profile.json`, so the empty-seed path
   cannot carry it either.
4. `[REQ-SB-95-US-01-AC-06]` Export the same selection with and without a saved
   Profile and assert the two payloads are byte-identical — the Profile's
   existence changes nothing that travels.

**Manual verification steps:**

1. `[REQ-SB-95-US-01-AC-06]` With the backend running and a real Profile saved
   naming at least one colleague, export a real bundle containing an Agent from
   the Artifacts screen; open the `.sbf` and confirm there is no
   `Operator/Profile.json` entry anywhere in it.
2. `[REQ-SB-95-US-01-AC-08 — DISCLOSURE ONLY, non-blocking, changes nothing]`
   In the same real bundle, search `agents/<id>/soul.md` and the extracted
   `agents/<id>/profile.tar.gz` for each colleague name and address from the
   Profile. Record both results verbatim in the Implementation Log — found or
   not found, per file. **Do not fix either result**; this is evidence for the
   operator's pending strip-vs-accept decision, and the task is not blocked by
   whatever it finds. Export through the running server (`MEMORY.md`:
   `registry_loader.agent_data_dir()` returns `None` until
   `registry_loader.boot()` has run in-process, so a raw script silently loses
   `Agent.json`/`soul.md`).

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The Profile is provably not an exportable artifact, and a guard keeps it so
- [x] No `Operator/` payload, no `Profile.json` seed entry, in any bundle
- [x] Everything that travels today still travels byte-identically
- [x] The disclosure for AC-08 is recorded, with no behaviour changed — against a
      **scratch-store** bundle, not the operator's real one (see the log)
- [x] `MEMORY.md` — a new constraint emerged and could NOT be appended: the file is
      86 KB against the 40 KB budget its own rule 1 sets, which forbids appending
      while over. Recorded in `REVIEW-QUEUE.md` instead, with the constraint text.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Stripping the `## Who you work for` block on export, or any other
  implementation of AC-08 — blocked on the operator's decision.
- Changing `ADR-014`'s opaque-bytes treatment of `profile.tar.gz`.
- Export/import of Actions and Workflows — `REQ-SB-95-US-02-T04` /
  `REQ-SB-95-US-04-T04`.

---

## Context / Notes

`ADR-032` (the Profile is excluded from artifact export by default) and
`ADR-014` (the agent profile tarball is opaque bytes) are the two authorities
here, and the gap between them is exactly the open question. The story's
`## Notes` → *Decomposer RE-pass* records the finding in full; `REVIEW-QUEUE.md`
carries the decision.

---

## Implementation Log

**2026-10-18 — coder. The guard passed unchanged; `artifact_export.py` was NOT
edited.** One file written:
`src/backend/tests/test_operator_profile_not_exported.py` (new, 5 tests).

### The finding the task's own conditional turns on

`AC-06` **already holds by construction**, exactly as `REQ-SB-95-US-04-T04`
established for `ActionCalls/`/`WorkflowRuns/` (`ADR-033`/`ADR-034`), and the
Operator store is in the same structural position. Read directly, confirmed by
test:

- `artifacts_inventory.list_all_artifacts()` composes **seven** Managers and
  produces no eighth `kind` — there is no `operator`/`profile` kind to select.
- `artifact_dependency_resolver.resolve_closure()` dispatches on those seven
  `kind` values and **silently resolves nothing** for any other — so the Profile
  cannot arrive as another artifact's dependency either.
- `artifact_export._PAYLOAD_FOLDER` maps no kind to the Operator store, and every
  payload key is built from `f"{_PAYLOAD_FOLDER[kind]}/{id}/"` — there is no code
  path that writes a `data/Operator/` byte.
- `artifact_seed_data.seed_data_files()` is **plugin-registered**, and nothing
  registers the Profile; and even if something did, `_add_seed_data_entries()`
  forces every seed member's content to `b""`, never reading the real file.

So the deliverable is the guard, as the task anticipated. **Zero production
change** — `artifact_export.py` is byte-identical to commit `2f91bb4`.

### How the guard is written to survive the eighth artifact kind

`ESC-077`'s rule (a negative test must pick an example nothing plans to build, or
derive it from the live set) is the design constraint here, so nothing in the
file is hand-maintained:

1. **Where the Profile lives is derived**, not spelled: `the_profile_store()`
   reads `operator_profile_data.profile_path()` relative to the data path. Move
   the store and the guard moves with it; no literal `"Operator"` in any
   assertion.
2. **What is exported is derived from the live inventory**
   (`everything_this_install_offers()`), so an eighth kind joins the exported
   selection automatically, with nobody remembering to extend a tuple.
3. **What counts as personal data is derived from the record as really stored** —
   every leaf string of `Profile.json`. A field added to the Profile in a later
   task is guarded the day it is added.
4. **The rule is a containment equality, not an absence**: the ONLY bundle member
   allowed to carry a Profile value is the exported agent's own `soul.md`
   (`AC-08`, accepted by the operator 2026-10-17). Any **other** member carrying
   one — an eighth kind sweeping `data/Operator/`, a new seed path, a new mirror —
   fails. That is the assertion that cannot go stale in the quiet direction.
5. The one frozen-looking assertion is a **lower bound** (`>= {the seven kinds}`),
   which an eighth kind cannot break and a removed kind correctly flags as a stale
   fixture.

**Proved non-vacuous by mutation, not by inspection.** A throwaway copy of the
file (scratchpad, outside the repo, never committed) added a plausible eighth
kind that treats `data/Operator/` exactly as `data/Actions/` is treated — listed
in the inventory, resolved into the closure, written into the payload. **Four of
the five tests failed**; the fifth (seed data) correctly did not, being a
different door. Without that probe, "5 passed first try" would have been
indistinguishable from a guard that asserts nothing.

### Locked AC — observed outcome

**`[REQ-SB-95-US-01-AC-06]` — PASS, all four automated steps + the manual step
(substituted onto a scratch store, see Deviations).**
`pytest tests/test_operator_profile_not_exported.py` → **5 passed in 2.48s**.

1. *No kind for it, no closure for it* —
   `test_the_profile_is_not_an_artifact_kind_and_no_selection_can_name_it`:
   with a real Profile saved under a tmp data path, the live inventory's kind set
   contains none of the names derived from the store (`operator`, `profile`,
   `operator_profile`), no `_PAYLOAD_FOLDER` value equals the store folder, and
   `resolve_closure()` returns `[]` for every one of those names. Not vacuous:
   `profile_exists()` is True and all seven kinds are really on offer.
2. *A bundle of every live kind* —
   `test_a_bundle_of_every_live_kind_carries_nothing_of_the_profile`: a real
   `.sbf` is written to disk and read back as **archive members** (not the
   in-memory payload — a file can be absent from the manifest and present in the
   archive). Observed: no member under the store folder, no member named
   `Profile.json`, no manifest artifact naming it, and the stored record's own
   bytes in no member. Every one of the seven selected kinds contributed payload
   (positive control).
3. *Seed data* — `test_no_seed_data_entry_names_the_profile` over the live
   `seed_data_files()`, plus
   `test_even_a_seed_entry_naming_the_store_carries_no_byte_of_the_record`, which
   forces a hostile registration of the Profile's own store path and observes the
   member arrive as `b""` with no personal value anywhere in the bundle.
4. *Byte-identical with and without a Profile* —
   `test_what_travels_is_byte_identical_with_and_without_a_saved_profile`:
   `payload_after == payload_before`, and the manifest's `artifacts` and
   `secret_scan` blocks equal. The Profile's existence changes nothing that
   travels.

**Manual step 1 (`AC-06`), substituted onto a scratch store — PASS.** A real
`.sbf` built by `commit_export` from a scratch install and opened as a real zip.
Its complete member list, verbatim:

```

actions/list-team-actions/Action.json          (374 bytes)
agents/blue-agent/Agent.json                   (68 bytes)
agents/blue-agent/profile.tar.gz               (34 bytes, inert stand-in)
agents/blue-agent/soul.md                      (1572 bytes)
indexes/adnoc/Index.json                       (38 bytes)
pipelines/morning-sweep.json                   (133 bytes)
skills/vault-search/SKILL.md                   (47 bytes)
templates/Meeting/Template.json                (47 bytes)
workflows/mail-me-the-team-list/Workflow.json  (305 bytes)

```

No `Operator/Profile.json` entry anywhere in it — nine members, seven kinds.

### `[REQ-SB-95-US-01-AC-08]` — DISCLOSURE ONLY, non-locked, nothing changed

Recorded honestly, per file, as the task requires. **Note the decision this was
evidence for is already taken**: the story's `gate_reason` records *"operator
accepted the export carrying the team's names, 2026-10-17"*. Nothing here
implements either answer.

**(a) `agents/<id>/soul.md` — the Profile's values DO travel.** Observed on the
real scratch bundle, per value, as the set of members carrying it:

```

'Robin Fictional'         -> ['agents/blue-agent/soul.md']
'robin.alt@example.test'  -> ['agents/blue-agent/soul.md']
'robin@example.invalid'   -> ['agents/blue-agent/soul.md']
'Etc/UTC'                 -> ['agents/blue-agent/soul.md']
'blue@example.test'       -> ['agents/blue-agent/soul.md']
'Fictional Engineer'      -> ['agents/blue-agent/soul.md']
'green@example.test'      -> ['agents/blue-agent/soul.md']
'Fictional Designer'      -> ['agents/blue-agent/soul.md']
'amber@example.test'      -> ['agents/blue-agent/soul.md']
'Fictional Analyst'       -> ['agents/blue-agent/soul.md']

```

The member carries the whole `## Who you work for` block verbatim, including the
`### Their team` list of `` `email` -- role `` lines and the operator's own
address read from `SELF_EMAIL`. Exactly one member, every value, no exceptions.

**(a′) A load-bearing nuance the decomposer's note did not have, found by direct
reading and confirmed by test.** The export does **not** read the Hermes-side
`SOUL.md` the publication pass writes. It reads the **Registry-side mirror**,
`registry_loader.agent_data_dir(id)/soul.md`, and
`AgentManager.publish_operator_profile()` deliberately does **not** write that
mirror (its own docstring, `AC-07`: writing it would rebuild `Agent.json` from a
cheap roster read and blank every agent's `skill_ids`). So:

- Immediately after a Profile save and nothing else, the mirror is **stale** and
  the bundle carries whatever block the mirror last held — possibly none.
- `AgentManager.update()` **does** rewrite the mirror from the current Hermes-side
  soul (`agent_manager.py` ~l.1625), so the first ordinary agent edit after any
  publication bakes the then-current team roster into the exported mirror.
- That is why test 4 above is byte-identical and test 2 shows the full leak: both
  are real states of the same install, a `update()` apart. The leak is real but
  **arrives late and silently**, which is worth knowing when reading the
  accepted-risk decision.

**(b) `agents/<id>/profile.tar.gz` — NOT verified against a real tarball, and
deliberately so.** `ADR-014` fixes it as opaque bytes and the task forbids
reaching inside it; this session is additionally standing-ordered never to touch
the operator's real Hermes install, and the suite sandboxes it. What can be said
from the code, without opening anything: `_export_agent_profile_tarball()` returns
the **raw unmodified** output of `HermesCLI.export_profile`, a Hermes profile
directory contains that profile's own `SOUL.md`, and that file is the one the
publication pass **does** write. So a second, *fresher* copy of the roster rides
in the tarball — fresher than the Registry mirror, since publication writes it
directly. Reported, not fixed, not asserted on.

### Deviations and scope-internal judgement calls (gate: flagged for spot-check)

1. **The two manual steps were performed against a scratch store, not the real
   one.** The task names "the backend running, a real Profile, export from the
   Artifacts screen". This session's standing conditions forbid building a bundle
   from the operator's real store, after three near-misses the same day. The
   substitute exercises the same real code end to end — a real `commit_export`, a
   real zip on disk, read back member by member — with fictitious data and a
   `tmp_path` install. `AC-06`'s claim is about what the exporter does, which this
   proves; what it does not prove is anything about the operator's own install's
   current contents.
2. **`artifact_export._export_agent_profile_tarball` is monkeypatched** to inert
   bytes in the guard. `tests/conftest.py` sandboxes Hermes suite-wide, so a real
   `hermes export-profile` cannot run and would raise. `ADR-014` makes those bytes
   opaque, so substituting them weakens nothing this task asserts — and the
   substitution is itself asserted (`payload[".../profile.tar.gz"] == THE_OPAQUE…`)
   so the member's presence is still pinned.
3. **The Registry-side mirror is written by the fixture**, from the genuinely
   published soul, to reproduce the post-`update()` state described in (a′) rather
   than a kinder one.
4. **No `MEMORY.md` entry could be written.** The constraint this task produced —
   *instance data is kept out of a bundle structurally (no kind, no folder), never
   by a name filter; a guard over it derives the forbidden thing from the live set
   rather than naming it* — is a real, reusable framework rule, but `MEMORY.md` is
   86,039 bytes against the 40 KB budget its own rule 1 sets, and that rule
   forbids appending while over. Routed to `REVIEW-QUEUE.md` with the text, as the
   eighth such blocked entry in four days.

### Suite

- **Baseline before the first edit:** `710 passed, 0 failed` in 44.23s
  (at `4837db9`).
- **After:** `733 passed, 0 failed` in 50.43s. 5 of the 23 new tests are this
  task's; the other 18 arrived from a concurrent session's commit `c88e016`
  (plugin tag namespaces) landing in the shared checkout mid-task. Zero failures
  either side; none of the four known order-dependent tests fired.

gate: flagged 2026-10-18 — trigger 1 only (scope-internal judgement calls above,
for spot-check). No locked AC unverified, no `ESCALATIONS.md` entry, no new
dependency, no shared interface changed, no ADR deviation, no unanticipated file:
one of the task's two listed files was written and the other, conditionally
scoped, was correctly left alone.
