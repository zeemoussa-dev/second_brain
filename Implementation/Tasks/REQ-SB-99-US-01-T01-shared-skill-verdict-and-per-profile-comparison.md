---
id: REQ-SB-99-US-01-T01
title: Extract the four-status verdict rule once, and add compare_profile_skills(profile_id) with a fifth unknown_to_framework status
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Done
gate: flagged
gate_reason: "Four scope-internal judgement calls logged for an optional spot-check; nothing is blocked."
phase: P2
depends_on: []
created: 2026-10-17
updated: 2026-10-18
---

# REQ-SB-99-US-01-T01 — One Verdict Rule, Two Enumeration Directions

## Parent Story

- Story: [[REQ-SB-99-US-01]] — `../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-99 *See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs*

---

## Objective

Give `SkillManager` a per-profile, install-first skills comparison that reuses
`check_deployment_drift()`'s own verdict rule rather than writing a second
answer to the same question.

---

## Starting State → End State

**Before / Inputs:**

- `src/backend/app/business/core/skills/skill_manager.py::check_deployment_drift()`
  (around line 425) enumerates `self.get_all()` × `skill.deployed_to` and decides
  `missing | current | stale | modified` inline, in the loop body
  (lines ~469-476). It is called only from `tests/test_versioning.py`.
- `client.skills.get_all(profile_id)` returns the real `HermesSkill`s found in
  that profile's own `skills/*/*/SKILL.md` tree, each carrying `.slug`, `.id`
  and `.version`; `client.skills.read(profile_id, skill_id)` returns the
  deployed bytes.
- `skills_data.read_skill_md(skill_id)` plus `self._frontmatter(skill_id)` give
  the catalog's bytes and its version.
- Matching is on **slug**, not `<category>/<slug>` — the catalog was regrouped
  by Tool on 2026-09-06 and deployed copies still sit under their old category
  (see the existing comment at line ~460).

**After / Outputs:**

- A module-level verdict function in the same file, e.g.
  `_deployment_verdict(deployed_md, deployed_version, catalog_md, catalog_version)
  -> str`, returning `current | stale | modified | missing` by exactly the
  existing precedence: nothing deployed → `missing`; bytes equal → `current`;
  versions differ → `stale`; otherwise → `modified`.
- `check_deployment_drift()` calls it. Its signature, its return shape, its
  catalog-first direction and its callers are unchanged;
  `tests/test_versioning.py` is the regression guard and must pass untouched.
- New `SkillManager.compare_profile_skills(profile_id: str) -> list[dict]`:
  walks **the profile's own tree** (`client.skills.get_all(profile_id)`), and
  for each deployed skill asks the catalog about it by slug. Rows carry at
  least `skill_id`, `slug`, `deployed_version`, `catalog_version`, `status`.
- A skill on disk whose slug the catalog does not have gets
  `status: "unknown_to_framework"` and `catalog_version: None` — a value the
  catalog-first direction structurally cannot produce.
- `deployed_to` is **not read anywhere** on the new path.

---

## Files to Modify

- `src/backend/app/business/core/skills/skill_manager.py` — extract the verdict
  rule; add `compare_profile_skills()`.
- `src/backend/tests/test_profile_skill_verdict.py` (new) — the tests below.

---

## Constraints

- Inherits from parent story.
- **One rule, two directions.** Do not copy the four-status logic into the new
  method; both call the extracted function. Two answers to "does the deployed
  copy match" is the failure this project has already paid for (`ADR-043`,
  Alternatives Considered; 228 stale copies of `vault_manager.py`).
- `check_deployment_drift()`'s external contract is frozen — same name, same
  signature, same row keys, same statuses, same enumeration direction.
- **Read-only.** No deploy, no `deployed_to` write, no
  `publish_section_access_map()`, no Registry mutation on this path.
- The Manager stays the sole gateway onto Skill data — callers of
  `compare_profile_skills()` never read skill bytes themselves.
- No new tree walk: reuse `HermesSkills.get_all()`'s existing two-level glob
  (`ADR-043` Consequences — this is what keeps the story free of new `MAX_PATH`
  exposure).

---

## Tests

**Automated tests:** `cd src/backend; pytest tests/test_profile_skill_verdict.py tests/test_versioning.py`

Use the existing fake-client technique from `tests/test_agent_listing_cost.py`
(`monkeypatch.setattr(client_module, "_client", fake_client)`) with a fake
`skills` object whose `get_all(profile_id)`/`read(profile_id, skill_id)` return
engineered content, and monkeypatch `skills_data.read_skill_md` for the catalog
side.

1. `[REQ-SB-99-US-01-AC-02]` Build a profile holding four skills — one
   byte-identical to the catalog, one whose version differs, one with the same
   version but different content, and one whose slug the catalog does not have.
   Assert `compare_profile_skills("adnoc-expert")` returns exactly four rows
   with statuses `current`, `stale`, `modified`, `unknown_to_framework`, each
   carrying the real `deployed_version` read off the profile's own tree.
2. `[REQ-SB-99-US-01-AC-02]` Assert the `unknown_to_framework` row carries
   `catalog_version: None` and is present *because* it is on disk — remove it
   from the fake profile tree and assert the row disappears, proving enumeration
   is install-first and not catalog-first.
3. `[REQ-SB-99-US-01-AC-02]` Pin that one rule serves both directions: with a
   catalog skill whose `deployed_to` names the profile and whose deployed bytes
   differ in version only, assert `check_deployment_drift()` and
   `compare_profile_skills()` report the **same** status string for that skill,
   and that `tests/test_versioning.py` passes unchanged.
4. `[REQ-SB-99-US-01-AC-05]` Give the fake client a `skills` object that raises
   on any write-shaped call (`write`, `deploy`, `undeploy`, `save`) and a
   `skills_data` whose write functions raise; call
   `compare_profile_skills("adnoc-expert")` and assert it returns normally —
   nothing on this path writes. Assert as well that no row's production required
   reading `deployed_to` (set the fake catalog skills' `deployed_to` to a
   sentinel that raises on iteration).
5. `[constraint: cost]` Assert `compare_profile_skills("adnoc-expert")` calls
   `skills.get_all` exactly once, and only with `"adnoc-expert"` — never once
   per catalog skill and never for another profile (`BUG-086` is the measured
   precedent for what the per-profile storm costs).

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The four-status rule exists once and both methods call it
- [x] `check_deployment_drift()` is contract-identical; `test_versioning.py` passes untouched
- [x] `compare_profile_skills()` enumerates install-first and adds `unknown_to_framework`
- [x] Nothing on the new path reads `deployed_to` or writes anything
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — none did (see Implementation Log, judgement call 4)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Reconciling or repairing `deployed_to` — `REQ-SB-96`.
- Deploying, undeploying or fixing a mismatched skill — `REQ-SB-96-US-02`.
- Any route or response shape — `T05`.
- A cross-profile comparison table — `REQ-SB-96-US-01`, from the other side.

---

## Context / Notes

`architecture.md` → **§Skills With Versions — Install-First Enumeration, One
Shared Verdict** and `ADR-043`. The story's own Context says the
skills-with-versions region is "the same fact seen from the other end" as
`REQ-SB-96-US-01`; `ADR-043` settles it as one rule with two enumeration
directions, and explicitly does **not** pre-empt `REQ-SB-96`'s open "which side
wins on a write" question — enumeration direction for a read is not authority
for a write.

---

## Implementation Log

_(Filled in by the coder.)_

**Verification mode:** automated (the backend has a real pytest stack).
**Baseline measured before any edit, at `4b450d1`:** `511 passed, 0 failed` in
20.76s — both known flakes (`test_health_check.py::test_health_reports_the_
commit_the_running_code_was_loaded_from`, `test_marketplace_source.py`) passed.
**After:** `516 passed, 0 failed` in 22.12s. New tests:
`tests/test_profile_skill_verdict.py` (5).

### AC-tagged outcomes

| AC-ID / tag | Test | Observed |
|---|---|---|
| `REQ-SB-99-US-01-AC-02` | `test_every_skill_on_disk_gets_its_verdict_and_its_real_deployed_version` | **Pass.** A profile holding four skills returns exactly four rows — `current`, `stale`, `modified`, `unknown_to_framework` — each with the version read off the profile's own tree (`1.0.0` / `0.9.0` / `2.0.0` / `0.1.0`), and `skill_id` is the `<category>/<slug>` it really sits at (`outlook/email-capture`), not the catalog's Tool grouping. |
| `REQ-SB-99-US-01-AC-02` | `test_a_skill_the_catalog_never_heard_of_is_listed_because_it_is_on_disk` | **Pass.** The `unknown_to_framework` row carries `catalog_version: None`; removing that skill from the fake profile tree drops the row (4 → 3), so enumeration is install-first rather than catalog-first. |
| `REQ-SB-99-US-01-AC-02` | `test_both_directions_return_the_same_status_for_the_same_skill` | **Pass.** With a catalog skill whose `deployed_to` names the profile and whose deployed copy differs in version only, `check_deployment_drift()` and `compare_profile_skills()` both report `stale`, and agree on `catalog_version` and `deployed_version`. `tests/test_versioning.py` passes unchanged (its `test_drift_report_uses_the_documented_statuses` is the named guard on the extraction). |
| `REQ-SB-99-US-01-AC-05` | `test_nothing_on_this_path_writes_or_consults_deployed_to` | **Pass.** The fake Hermes `skills` object raises on `write`/`deploy`/`undeploy`/`save`/`create`/`update`/`delete` and `skills_data`'s `write_skill_md`/`write_script`/`write_section_access_map`/`delete_skill_dir` raise; `deployed_to` is a sentinel raising on `__iter__`/`__contains__`. `compare_profile_skills("adnoc-expert")` returns four rows normally. |
| `[constraint: cost]` | `test_one_profile_costs_one_listing_and_one_read_per_skill` | **Pass.** Pinned by equality, not by bound: `skills.get_all` calls `== ["adnoc-expert"]` (one listing, only that profile); catalog reads `== 4`, one per distinct slug; deployed-bytes reads `== 3` — none for the `unknown_to_framework` slug, since there is nothing to compare it against. |

### Where the reads and writes landed

Ran both test files, and then the whole suite, behind a scratchpad pytest plugin
wrapping `pathlib.Path`'s read primitives (`read_text`, `read_bytes`, `open`,
`iterdir`, `glob`, `rglob`, `stat`, `exists`, `is_dir`, `is_file`) and its write
primitives (`write_text`, `write_bytes`, `mkdir`, `unlink`, `rmdir`, `rename`,
`replace`, `touch`, `chmod`) plus `subprocess.run`/`Popen`, recording anything
under the **real** `<HERMES_HOME>` captured at import time before `conftest.py`'s
sandbox applies:

- `tests/test_profile_skill_verdict.py` + `tests/test_versioning.py`:
  **0 reads, 0 writes, 0 subprocesses** under the real install.
- Full suite: **0 reads, 0 writes** under the real install (152 subprocess
  spawns, all pre-existing `git` calls from the plugin/marketplace tests against
  their own `tmp_path` repos — none from these files).

`conftest.py` was neither weakened, bypassed nor special-cased.

### Judgement calls (scope-internal, logged for spot-check)

1. **`_frontmatter_of(md)` extracted alongside `_deployment_verdict`.**
   `self._frontmatter(skill_id)` re-reads the catalog's `SKILL.md` to get the
   version, which on the new path would have been a second disk read per skill
   on top of the one for the bytes. The parse is now a module-level function
   over an already-read string and `_frontmatter()` delegates to it — behaviour
   identical, catalog reads halved. `ADR-043` budgets "two file reads per skill"
   (deployed bytes + catalog bytes), which this keeps to.
2. **A `missing` row's `deployed_version` is `None` on both paths.** The
   install-first direction can still produce `missing` — a `SKILL.md` the glob
   saw whose bytes then fail to read — and it reports it the same way
   `check_deployment_drift()` always has, rather than inventing a sixth status.
3. **No deployed-bytes read for an `unknown_to_framework` skill.** There is no
   catalog copy to compare it against, so the read would be pure cost. Its
   `deployed_version` still comes off the tree, from `get_all`'s own frontmatter
   parse.
4. **No `MEMORY.md` entry.** The decision this task executes is already written
   down as `ADR-043` and in `architecture.md` §Skills With Versions; nothing new
   and framework-wide emerged that is not already there.

Nothing was written to `REVIEW-QUEUE.md` or `ESCALATIONS.md`; no file outside
`## Files to Modify` was touched (plus `CHANGELOG.md` and the status
propagation this task's contract allows).
