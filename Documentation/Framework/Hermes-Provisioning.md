# `Hermes-Provisioning/` — retired 2026-09-06

**This folder no longer exists.** Nothing depends on it, and nothing should be
brought back. This page is kept only so the name resolves to an answer instead
of a dead reference.

It used to be the canonical source for the Hermes side of the system — the
Skills, the shared engine, the provisioning config — deliberately held *outside*
the working tree so it was not read as a standing part of the project.

That arrangement was the problem. `data_access/skills.py` resolved Skill content
through it, so while it was absent `SkillManager.get_all()` returned **0** and
`GET /skills` returned `[]` **silently** — an empty Skills list read as "no
Skills exist" rather than "the source is not here". Skills are backend-owned
framework content; they now live with the rest of it.

## Where its contents went

| Was | Now |
|---|---|
| `skills/<category>/<slug>/` | `src/backend/app/business/core/skills/catalog/<tool>/<slug>/` — grouped by **Tool** |
| `shared/vault_manager.py` | `.../skills/managers/vault_manager.py` — **one** canonical copy |
| `shared/build_vault_index.py` | `.../skills/managers/build_vault_index.py` |
| `config/custom_providers.yaml` | [`hermes/custom_providers.yaml`](hermes/custom_providers.yaml) |
| `cron/meeting-prep-agent.md` | [`hermes/meeting-prep-agent.md`](hermes/meeting-prep-agent.md) |
| `mcp-servers/outlook.yaml` | **dropped** — dead since the MCP Tool layer was removed (`49f064f`) |

The one piece worth reading before touching Hermes' own `config.yaml` is the
Compass provider entry: its `base_url` must **not** be the full completions URL,
because Hermes appends `/chat/completions` itself, and there are two `base_url`
fields for the same logical provider of which only `custom_providers[]` is
actually read. That trap is documented in
[`hermes/custom_providers.yaml`](hermes/custom_providers.yaml).

## What replaced the "prepare here, apply there" discipline

It survives, but for **one file instead of a folder**. The shared engine is
deployed to `<hermes_home>/managers/` and put on `PYTHONPATH` via Hermes' own
`.env`; `SkillManager.deploy()` refreshes it on every deploy. A Skill does not
carry its own copy, because a local copy silently wins over `PYTHONPATH`
(`sys.path[0]` is the script's own directory) — which is exactly how 228 stale
copies came to run across 41 profiles.

See [`ADR-019`](../../Implementation/Architecture/ADR.md) for the full decision
and [`Artifacts.md`](Artifacts.md) for the artifact shapes.
