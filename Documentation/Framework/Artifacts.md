# Artifacts — what the framework is made of, and what moves between installs

Four things are **artifacts**: **Template**, **Agent**, **Skill**, **Pipeline**.
They are what you author to extend the system, and what travels between installs
in a `.sbf` bundle.

Verified against the code, 2026-09-04. Templates have their own guide —
[Templates.md](Templates.md).

---

## Where everything lives

Everything below is under `<SECOND_BRAIN_DATA_PATH>` — the app database folder,
deliberately independent of the vault so it can be relocated without moving
notes.

```
data/
  Templates/<id>/Template.json
  Sections/<section>/Section.json
  Sections/<section>/Agents/<agent>/Agent.json   + soul.md
  Background/Agents/<agent>/Agent.json           + soul.md   # agents outside any Section
  Tools/<tool>/Tool.json
  Tools/<tool>/Skills/<skill>/Skill.json         + Skill-visual.json
  Providers/<provider>/Provider.json
pipelines/<id>.json                                          # note: NOT under data/
```

Two things worth noticing: a **background agent lives outside any Section**
(`Background/Agents/`), and **Pipelines sit at the top level**, not under `data/`.

---

## Agent

The Agent is the one artifact with **two homes**. Its identity, model, prompt and
skills are Hermes' own data (the profile); the Registry adds the parts Second
Brain owns.

| Field | Meaning |
|---|---|
| `id` | The real Hermes profile folder name — the shared key on both sides |
| `name`, `description` | From Hermes' `profile.yaml` |
| `type` | `worker` \| `producer` \| `expert` \| `hub` |
| `section_id` | Where it sits on the Agents Map. **`null` is valid** — an unplaced agent is simply unplaced |
| `is_background_agent` | Background agents are stored outside Sections and de-emphasised on the map |
| `working_mode` | `autonomous` \| `human_in_loop` |
| `model`, `reasoning_effort` | From Hermes' `config.yaml` |
| `prompt`, `guardrails`, `scope` | Composed into **one** real `SOUL.md`, not stored as separate Hermes fields |
| `scope` | `{"folders": [...], "tags": [...]}` — vault data access, distinct from `section_id` (identity) |
| `skill_ids`, `tools`, `depends_on`, `preferred_index_ids` | Wiring |
| `primary_routing_snippet` | How the primary agent decides to route to it |

`soul.md` in the Registry is a **one-way mirror** of the real Hermes `SOUL.md`,
never a second source of truth.

> Second Brain cannot bootstrap Hermes. Hermes' profiles are the source; the
> Registry annotates them.

---

## Skill

A Skill is a `SKILL.md` plus a `scripts/` folder, invoked through Hermes' own
`terminal` tool. Its data is deliberately split across two stores: the filesystem
holds the content, the Registry holds the metadata.

| Field | Meaning |
|---|---|
| `id` | Slug, globally unique across every category |
| `category` | The folder grouping it lives under |
| `tool_id` | The owning Tool grouping; `None` until assigned |
| `mutates` | Whether it writes anything |
| `origin` | `second-brain` (authored here) \| `jarvis` (synced in) |
| `deployed_to` | The real Hermes profile ids it is currently pushed to |

**A Skill is inert until copied to a real Hermes profile.** Editing it in the
repo does nothing to a live install by itself.

> **Not present in the working tree by default.** `Hermes-Provisioning/` is held
> outside the checkout on purpose (operator, 2026-09-04) so it is not read as a
> standing part of the project — it still exists and is brought back when needed.
> While it is absent, `data_access/skills.py` finds no Skill content and
> `GET /skills` returns `[]` **silently**, so an empty Skills list means "the
> source is not here right now", never "no Skills exist". See
> [Hermes-Provisioning.md](Hermes-Provisioning.md) for exactly what needs it.

---

## Pipeline

A Pipeline is a hand-edited JSON definition at `<data>/pipelines/<id>.json`,
composed at read time with live cron state from Hermes.

| Field | Meaning |
|---|---|
| `id`, `name`, `description` | Identity |
| `section_id` | Resolved from a plain Section **name** string on disk |
| `steps[]` | `{id, name, description, depends_on[], type}` where `type` is `worker` \| `producer` |
| `cron_*` | Read live from Hermes — job id, profile, schedule, last/next run, status. Not stored |

> A step's `id` carries **no** Agent or Skill linkage. It exists only to draw the
> dependency tree.

> **Watch out:** resolving a Pipeline's Section **creates** it if the name does
> not exist. On an install with no Sections, importing a Pipeline will therefore
> mint one.

---

## Moving artifacts between installs

### The three archive formats — do not confuse them

| Format | Carries | Built by |
|---|---|---|
| **`.sbf`** | Artifacts — Template, Agent, Skill, Pipeline | `artifact_export.py` / `artifact_import.py` / `sbf_archive.py` |
| **`.sbb`** | Hermes structural backup — profiles, cron, skills | `tools/hermes_backup.py` / `hermes_restore.py` |
| **`.sbd`** | Real vault **data** (the notes themselves) | `sbd_archive.py` |

### What export does

1. **Dependency closure** (`artifact_dependency_resolver.py`) — exporting a Skill
   pulls in the Templates it needs, so a bundle is self-sufficient.
2. **Secret scan** (`artifact_secret_scan.py`) — before anything leaves.
3. **Placeholder substitution** — machine-specific **absolute** paths are
   replaced with tokens so content is portable.

### What import does

- Gates on an **explicit per-artifact decision** the moment `conflicts: true`,
  returning an honest `"failed"` outcome naming the missing decision rather than
  defaulting silently (`artifact_import_conflicts.py`).
- Dispatches per kind inside the caller's own `try/except`, so one artifact
  failing does not abort the rest.
- Asks explicitly where an incoming **Agent** should be placed, rather than
  silently choosing a Section.

### Three limits worth knowing before you rely on it

- **Placeholder substitution cannot catch a hardcoded *relative* path.** It
  substitutes absolute paths; a relative one travels intact and breaks quietly.
- **A restore recreates no `.env` anywhere.** Backup excludes every one as a
  secret, so a restored install has its structure and none of its environment —
  the setup wizard is what puts that back.
- **Exporting an Agent drops part of its own `Agent.json`** — a confirmed
  constraint, not a hypothesis.

---

## Which artifact do I actually want?

| I want to… | Author a… |
|---|---|
| Store a new *kind of note* | **Template** — never new code |
| Give an agent a new capability it runs | **Skill** |
| Add a new specialist that reasons | **Agent** (a Hermes profile, annotated here) |
| Run something on a schedule, in steps | **Pipeline** + a Hermes cron job |
