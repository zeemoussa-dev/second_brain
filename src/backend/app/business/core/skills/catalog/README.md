# Skill catalog — the shipped Skills, grouped by Tool

A **Skill** is `SKILL.md` + `scripts/`, executed inside Hermes through its
`terminal` tool. It is **inert until deployed** into a Hermes profile: editing
one here does nothing to a running install.

Layout is `catalog/<tool>/<slug>/`. The grouping folder is the **Tool** — the
capability domain the Skill acts through.

## Why these are here

Until 2026-09-06 this lived in `Hermes-Provisioning/skills/`, a folder held
*outside* the checkout. While it was absent `SkillManager.get_all()` returned 0
and `GET /skills` returned `[]` **silently** — an empty Skills list read as "no
Skills exist" rather than "the source is not here". Skills are backend-owned
framework content, so they now live with the rest of it.

## How the Tool was decided

From what each Skill actually depends on, **not** from the Registry's grouping —
that had six of our own Skills mis-filed under the catch-all `jarvis` Tool,
because we deploy Skills by hand, Hermes becomes the de-facto source of an
Agent's `skill_ids`, and `sync_from_hermes()` then reads our own Skills back as
foreign.

| Tool | How it was determined |
|---|---|
| `vault` (14) | resolves `vault_path` / `data_root` and writes notes |
| `outlook` (2) | the only two importing `outlook_lib` |
| `pricing` (1) | queries `prices.azure.com`; touches no vault at all |

## Shared libraries are not carried per skill

`vault_manager.py` is **not** stored in a Skill's `scripts/`. One canonical copy
lives in `../managers/` and is materialised into each profile at deploy time,
into exactly the Skills whose scripts import it — the same "prepare here, apply
where it's needed" shape `deploy_index_builder()` already uses.

The repo previously carried **16 copies in 5 different versions**. That is not a
tidiness point: it is how `index_builder_lib` stayed on `rglob` for weeks after
the MAX_PATH fix landed in a *different* copy, and it is the same shape as the
2026-09-04 `data_root` outage.

**Still duplicated, deliberately:** `outlook_lib.py` and `vault_lib.py` each
exist twice and have **already drifted** between `email-thread-capture` and
`meeting-capture`. De-duplicating those needs a real merge decision, not a file
move, so they were left alone rather than blind-merged.

## Tests

A Skill's own tests live beside its scripts and run in the flat shape a deployed
Skill has (see the `conftest.py` that supplies the managers directory). They are
**not** collected by the backend suite — see `pytest.ini` for why and for how to
run them.
