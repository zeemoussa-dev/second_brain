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

> **Emptied 2026-09-06 (operator-directed), starting a clean cross-device build.**
> This file carried 63 entries / 5,035 lines, 36 still `Open`, the oldest from
> 2026-08-11.
>
> **This one is a deliberate exception to the file's own rule.** It is designed
> append-only precisely so the record of backward steps survives; emptying it is
> the operator's call for a fresh build phase, not a change to that rule. The
> rule still stands for everything logged from here on.
>
> **Nothing is lost** — the full log is in git at `d64dcb4`:
>
> ```bash
> git show d64dcb4:ESCALATIONS.md
> ```
>
> **The next id is `ESC-063`.** Ids are never reused; the historical ones are
> still referenced from stories, tasks and ADRs.

---

## ESC-063: `ADR-032`'s entity resolver and `ADR-022`'s Entities-plugin boundary disagree — 2026-10-16

**Category:** adr-deviation
**Trigger:** Specing `REQ-SB-95` (analyst, `/spec`) produced
`REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`, which cannot say which
repository it builds in. `ADR-032` (Accepted 2026-10-16) specifies entity
resolution as "ONE tag-keyed index, not one index per entity. A single artifact
groups every `customer/*` and `partner/*` tag" — written as framework work, and
spelt out nowhere as anything else. `ADR-022` (Accepted 2026-09-14) decides the
opposite boundary for exactly those concepts: "the Customer, Partner and
Opportunity code moves into a Entities plugin (`sb-plugins-entities`) together
with `Entities.md`, its Settings page, the company Skills and `company_index`",
and "Core never imports, names or knows a plugin", under the operator's own test
that *a second brain built for a CFO cares nothing about Partners and Customers*.
The contradiction is not theoretical: `Settings/Entities.md` is already reached
through `app/plugin_api.py`'s `register_seed_data_file()`, i.e. it is already
being handled as plugin-owned seed data, while `ADR-032` assumes a resolver that
reads it. The two readings land the work in different repositories, under
different `CLAUDE.md`/`MEMORY.md` contexts (`ADR-023`), with different answers to
whether a non-Customer/Partner install gets the feature at all.
**Resolution:** Operator, 2026-10-16: "Resolver is framework, Customer stays the
plugin." The framework ships a tag-keyed resolver generic over any `<namespace>/<slug>`
tag, naming no plugin and knowing nothing of Customers; a plugin registers its namespace
through the Plugin API, and the entities plugin registers `customer/` and `partner/`.
`REQ-SB-95-US-05` therefore builds in this repository as mechanism, with the namespace
registration belonging to `sb-plugins-entities`. `ADR-022` stands unamended -- core offers
a seam, the plugin fills it.
**Resolving artefact:** `ADR-035`
**Status:** Resolved

---

## ESC-064: `REQ-SB-95-US-02-T02` needs a file `T01` owns — save-time resolution makes one of `T01`'s own tests fail — 2026-10-16

**Category:** out-of-scope-file
**Trigger:** `REQ-SB-95-US-02-T02` adds `ADR-032`'s save-time implementation
resolution to `ActionManager.create()`/`update()`. `T01` (Done, commits
`4ecd43c`/`8fd50bb`) wrote `src/backend/tests/test_action_artifact_kind.py`
before that gate existed, and its `AC-01` round-trip test saves an Action
against `implementation={"skill": {"skill_id": "vault-search"}}`. `vault-search`
is catalogued in this repo and deployed to **no** Hermes profile
(`SkillManager().get_by_id("vault-search").deployed_to == []`, measured), so the
new gate correctly refuses that save and the `T01` test fails:

```
FAILED tests/test_action_artifact_kind.py::test_a_saved_action_round_trips_everything_the_operator_authored
ActionImplementationUnresolvedError: this Action's skill implementation does not
resolve on this install: skill 'vault-search' is not deployed on this install
```

`T02`'s `## Files to Modify` names only `action_manager.py`, `action.py` and the
new `tests/test_action_resolution.py`. `test_action_artifact_kind.py` is not in
it, so fixing the failure is an out-of-scope edit (Pipeline.md hard rule 5), and
the coder stopped rather than improvising a change to a `Done` task's test.

**The two constraints are jointly unsatisfiable without a human**: "`AC-02`
refuses a catalogued-but-undeployed Skill" (locked, verified green) and "the
suite stays green" cannot both hold while that `T01` test stands. This is a
decomposition gap, not a disagreement about behaviour — nothing in `ADR-032`,
`ADR-033` or the story is contradicted, and `T02`'s own locked ACs (`AC-02`,
`AC-07`) pass on nine new AC-tagged tests.

**What the fix is:** `test_a_saved_action_round_trips_everything_the_operator_authored`
needs the same resolution-source monkeypatch the new `tests/test_action_resolution.py`
already uses (`deployed_skill_ids` / `app_route_table` / `UI_FEATURE_KEYS` on
`app.business.core.actions.action_manager`), or its `"vault-search"` swapped for
a really-deployed slug. Roughly five lines; it asserts nothing about resolution,
so `AC-01`'s meaning is untouched either way. Whoever authorises it should add
that file to `T02`'s `## Files to Modify` (or mint a `T02a`) rather than letting
a coder reach outside its scope by precedent.

**Resolving artefact:** —
**Status:** Open
