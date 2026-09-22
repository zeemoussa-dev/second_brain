# Building a Skill

A **Skill** is what an agent can actually run: instructions in `SKILL.md` plus the
scripts that carry them out. **Tool → Skills → Actions** — a Tool groups Skills,
a Skill performs Actions.

Build a Skill when an agent needs to *do* something. If you only need to store a
new kind of note, you want a [Template](Templates.md) instead — never a script.

Read [Artifacts.md](Artifacts.md) for the Skill's shape and where its two halves
live. This page is the walk-through.

---

## Before you start

- **A Skill is inert until it is deployed.** Editing it in the repo changes
  nothing on a live install until it is pushed to real Hermes profiles.
- **A Skill never carries a shared engine.** `vault_manager.py` and the other
  managers are materialised into `<hermes_home>/managers/` and imported by bare
  name. Bundling a copy into `scripts/` silently wins over the shared one
  (`sys.path[0]` is the script's own folder) — that is how 228 stale copies once
  ran across 41 profiles.
- **Every write goes through the engine and a Template.** A script that formats
  its own markdown is the wrong answer.

---

## 1. Write the content

Framework Skills live in the repo at:

```
src/backend/app/business/core/skills/catalog/<tool>/<skill-id>/
    SKILL.md
    scripts/*.py
    scripts/tests/test_*.py
```

The folder under `catalog/` is the **Tool** the Skill acts through (`vault`,
`graph`, …), not a free-form category.

### `SKILL.md`

The instructions Hermes gives the agent, with frontmatter the framework reads:

```yaml
---
name: capture-files
description: Catch-all capture for a file uploaded with no stated context.
version: 0.2.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, files, quick-capture]
writes:
  - action: capture_file
    template: file
    requires: 1
    sections: [Summary, Details]
---
```

`writes:` is the part with teeth. It declares which Actions write which sections
of which Template, and `requires:` is the Template **content version** it was
written against. Deployment validates that declaration against the real Template
on the install and **refuses** on a mismatch — an exact match, not `>=`: a bump
means a section was renamed or removed, so an older Skill is wrong, not merely
behind.

The body is prose for the agent: what the Skill is for, its prerequisites, and
one numbered "Job" per Action, each naming the exact command to run.

### `scripts/`

Plain Python, run through the Hermes toolset's `terminal`. Conventions that
matter:

- **Sibling imports only** (`import vault_manager as vm`). A deployed Skill is
  flat.
- **Take `--vault-path` on every call**; never hardcode a vault or data path.
  Resolve the app database folder with `vm.data_root(vault_path)`.
- **Long paths**: use the engine's `long_path` for every filesystem call. Past
  260 characters Windows returns *false*, not an error (a whole day of email
  capture was lost to this).
- **Idempotent**: re-running re-derives from what is on disk. A note is keyed on
  a stable `id`, so a second run updates rather than duplicates.
- **Honest failure**: report what failed and keep going; never write a
  half-understood shape.

---

## 2. Test it

Put tests in `scripts/tests/` with a `conftest.py` that puts the script folder
and the shared managers on `sys.path` — the tests import exactly what the
deployed Skill imports:

```python
_SCRIPTS = Path(__file__).resolve().parent
for path in (_SCRIPTS, _MANAGERS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
```

Where `_MANAGERS` points depends on which repository the Skill lives in — see
[Skills in an agent repository](#skills-in-an-agent-repository).

Run them with the backend's interpreter from the Skill's `scripts/` folder:

```bash
src/backend/.venv/Scripts/python.exe -m pytest -q
```

---

## 3. Register it

The content is half a Skill; the Registry holds the other half at
`<app data>/data/Tools/<tool>/Skills/<skill-id>/Skill.json`:

| Field | Meaning |
|---|---|
| `id` | The slug, unique across every Tool |
| `tool_id` | The owning Tool |
| `mutates` | Whether it writes anything |
| `origin` | `second-brain` (authored here) or `jarvis` (synced in) |
| `deployed_to` | The real Hermes profile ids it is currently pushed to |

---

## 4. Deploy it

Deployment pushes the current content to real profiles:

- **`deploy(skill_id, profile_id)`** adds it to one more profile. It validates
  `writes:` first and raises rather than deploying a Skill whose Template is
  missing or a different version.
- **`redeploy(skill_id)`** pushes current content to **every** profile the Skill
  is already on. This is what you want after editing a deployed Skill.

Both refresh the install's shared managers and rebuild `section_access.json`, the
derived map that tells the engine which Action may write which section.

Check what is actually out there with `SkillManager.check_deployment_drift()`:
every profile reports `current`, `stale`, `modified` or `missing`. A Skill edited
in the repo and never redeployed shows as `stale` on every profile — that is the
usual explanation for "I fixed it but the nightly run still does the old thing".

---

## Skills in an agent repository

Business Skills do not belong to the framework. They live in an agent repository
(`sb-pss-agent`), which **is** that install's config folder, laid out the same
way: `data/Tools/<tool>/Skills/<skill-id>/`.

Two consequences:

- **Shared engines come from two places.** The framework's (`vault_manager.py`,
  `history_log.py`) exist only on an install, in `<hermes_home>/managers/`. An
  agent repository ships its own in `data/managers/*.py` (for example
  `company_index.py`), and `deploy_shared_managers` copies those into the same
  folder — refusing any file named like a framework manager, which would
  silently replace the framework's engine for every Skill.
- **Its tests run against the framework's source**, through the framework's own
  resolver -- see [Testing a Skill outside the framework](#testing-a-skill-outside-the-framework).

> **Known gap.** The framework deploys Skills from its **own** catalog only. A
> Skill living in an agent repository has to be deployed by hand today; there is
> no "deploy from the config folder" path yet.

### Testing a Skill outside the framework

A Skill in an agent repository imports what it imports when deployed -- the
framework's shared engines, its own repository's engines, Master Templates -- and
none of them sit beside it. The framework answers "where are they" once, in
`src/backend/skill_testing.py` (`BUG-069`). **One setting** points at it:

| Setting | Meaning |
|---|---|
| `SECOND_BRAIN_FRAMEWORK` | The framework checkout to test against. Unset: a `second_brain` checkout in any folder above the Skill. |

Each Skill's `scripts/conftest.py` finds the checkout, loads the resolver by path,
and calls `configure(__file__)`:

```python
_PATHS = _load_resolver().configure(__file__)

master_template = _PATHS.master_template    # Path to <id>/Template.json
shared_engine = _PATHS.shared_engine        # Path to a shared engine file
engine_roots = _PATHS.engine_roots          # folders, for a subprocess's PYTHONPATH
framework_skill = _PATHS.framework_skill    # a framework Skill's scripts/, from the catalog
```

`sb-pss-agent` carries the full conftest; copy it rather than writing another. What
`configure` does:

- puts the Skill's own `scripts/`, the repository's `data/managers/` and the
  framework's shared managers on `sys.path`, **in that order**;
- finds the repository by its `.git` folder, never by counting parent folders;
- looks a Master Template up in the repository's `data/Templates/`, then the
  framework's masters, then each Marketplace plugin's newest package -- where
  business Templates such as `customer` moved with the Entities plugin.

Two deliberate choices:

- **The source, not a deployment.** Testing against the engines deployed to Hermes
  tests yesterday's deployment and passes on a stale copy; it also leaves a machine
  without an install testing nothing.
- **Missing is an error, not a skip.** A framework that cannot be found stops the
  run with the setting to fix. A suite that skips itself reports green while
  checking nothing -- which is how 24 tests went unrun.

---

## Traps

| Trap | What actually happens |
|---|---|
| Editing a deployed Skill and expecting it to take | Nothing changes until `redeploy`. Check drift. |
| Bundling `vault_manager.py` into `scripts/` | The local copy wins over the shared one, forever, silently. |
| A `writes:` version that drifts from the Template | Deployment refuses — by design. Bump the Skill with the Template. |
| Hardcoding a path | Absolute paths break on the next machine; a **relative** one survives export substitution and breaks quietly. |
| `"20m"` as a schedule | That is a **one-time** job. Only `"every 20m"` recurs. |
| A Skill that reaches for another Skill's folder | Search every category, and the install's deployed Skills, not just your own. |
| An agent Skill's test counting `parents[N]` to reach the framework | True only inside the framework's tree. Use `skill_testing.py`. |
| A test that skips when the framework or an install is absent | Reports green while testing nothing. Fail with the setting to fix instead. |

---

## Related

- [Artifacts.md](Artifacts.md) — the Skill's shape, the two stores, the `.sbf` bundle
- [Templates.md](Templates.md) — the note type a Skill writes through
- [Building-a-Plugin.md](Building-a-Plugin.md) — when the thing you are adding is a screen or an endpoint, not an agent capability
- [Hermes-Runtime.md](Hermes-Runtime.md) — profiles, cron and the live install
