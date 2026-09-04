# How to Use the Framework

This is the reference for **using** Second Brain — for the person operating it and
for any agent working on it. Same document, same facts, no separate versions to
drift apart.

Read this first. It explains what the pieces are and how to do the common things.
The deeper reference pages are linked at the end.

---

## The idea in one paragraph

Second Brain turns an Obsidian vault into something agents can read and write
safely. **The vault is the database** — real markdown files you can open, edit and
keep, not a hidden store. Everything the system writes goes through **one engine**
that follows a **Template**: a small JSON file describing one kind of note. Agents
do the work, Skills are what they can run, and Pipelines run things on a schedule.

The rule that matters most:

> **A new kind of note is a new Template. Never new code.**

If someone is writing a script to produce a new kind of note, that is the wrong
answer.

---

## The pieces

| Piece | What it is |
|---|---|
| **Vault** | Your Obsidian folder. Real markdown files. The system reads and writes it directly — there is no staging or approval step, because it is your own trusted data. |
| **Note** | One markdown file, with frontmatter at the top and `## Sections` in the body. |
| **Template** | Defines one *kind* of note: where it goes, what it is called, which sections it has, and who may write each one. |
| **Section** | A grouping on the Agents Map — Customers, Sales, and so on. Agents live in one. A fresh install has **none**; you create the ones you want. |
| **Agent** | A specialist. Backed by a real Hermes profile — its own prompt, model and skills. `worker`, `producer`, `expert` or `hub`. |
| **Action** | One concrete operation — ingest an email, write a note, resolve a person. |
| **Skill** | A unit that performs Actions: instructions (`SKILL.md`) plus the scripts that carry them out. Inert until deployed to a real Hermes profile. |
| **Tool** | **A group of Skills managing a set of Actions.** The grouping layer — Tool → Skills → Actions. |
| **Pipeline** | A multi-step job with a dependency tree, usually on a schedule via a Hermes cron job. |
| **Index** | A scoped, pre-built view of the vault for agents to search — chosen folders, optional tag filter, depth limit, own refresh schedule. |
| **Provider** | An LLM endpoint and model. Listings only ever say *whether* a credential is set, never the secret itself. |

### The capability hierarchy — say it this way, every time

> **Tool → Skills → Actions.** A **Tool** is a group of **Skills** managing a set
> of **Actions**.

That is the settled vocabulary. Use these words in this order and nothing drifts.

**Do not confuse it with Hermes' own "tools".** Hermes has built-in capabilities
it also calls tools — `terminal`, `file`, `memory`, `browser` — which is a
*different vocabulary owned by a different system*. In this documentation those
are always **"the Hermes toolset"**, never "Tools". An Agent's `tools` field
refers to that Hermes toolset; a **Tool** in this framework groups Skills.

**One historical trap.** An earlier attempt exposed `Tool → Category → Action`
over MCP and was abandoned. The *taxonomy* was right and survives — that is why
dead MCP code can look like the live model. The MCP delivery mechanism is what
failed, and Skills became Hermes-native scripts instead. If you find MCP mounting
code, it is a remnant, not the design.

### Two more ideas people mix up

- **Section is identity, scope is access.** An agent's Section is where it *lives*
  on the map. Its `scope` (`folders` + `tags`) is what it may *read* in the vault.
  Changing one does not change the other.
- **The Registry annotates Hermes; it does not replace it.** An Agent's prompt,
  model and skills belong to its Hermes profile. Second Brain adds placement,
  type, wiring and visuals. It cannot create Hermes out of nothing.

---

## How to do things

### Capture a new kind of thing (emails, meetings, tickets…)

Write a **Template**, then point something at it. No engine changes.

1. Create `<app data>/data/Templates/<id>/Template.json`.
2. Decide the **identity key** — this is the important decision. Use the source's
   own stable id (a conversation id, an event id) as the note's `id`, and re-runs
   update the same note instead of creating duplicates.
3. Decide which sections the machine owns and which are yours.
4. Test it against a scratch vault before pointing it at the real one.

Full details, every key, and a worked example → **[Templates.md](Templates.md)**

### Stop agents writing your own notes

Declare the section `human_only` in the Template. The engine **refuses** the
write — it is not a prompt instruction an agent can drift away from.

> **Careful:** a section you *don't* declare defaults to open. Protection is
> something you opt into.

By convention `## Actions` and `## Personal Notes` are yours.

### Add a specialist agent

Create the Hermes profile first (it owns the prompt, model and skills), then set
its Section, type and wiring on the Agents Map. Cloning an existing profile
inherits everything, so trim it down to what that specialist should actually have.

### Give an agent a new capability

Author a **Skill** — instructions plus scripts — and deploy it to the profiles
that need it. A Skill sitting in the repo does nothing until it is copied into a
real profile.

### Run something on a schedule

A **Pipeline** describes the steps and their dependencies; a **Hermes cron job**
actually runs it.

> **Schedule syntax trap:** `"20m"` creates a **one-time** job. Only
> `"every 20m"` recurs. The success message looks nearly identical either way —
> read it, or check the job.

### Control what an agent can see

Set its `scope` — `folders` and `tags`. For search, give it an **Index**: pick the
folders, optionally require tags, set a depth limit and a refresh schedule.

### Move work to another machine

Export an **Artifact bundle** (`.sbf`). It resolves dependencies automatically —
exporting a Skill brings the Templates it needs — and scans for secrets first.

> Restores recreate **no** `.env` anywhere. A restored install has its structure
> and none of its configuration; the setup wizard puts that back.

Formats, field shapes and import behaviour → **[Artifacts.md](Artifacts.md)**

### Change the model

Providers hold the endpoint, model and credential. Every specialist profile
created by cloning inherits the default profile's model — **so configure the
default first**, then clone. Otherwise you fix the same setting on every profile.

---

## First run

The setup wizard asks for the vault path, your email address, and the model
endpoint. Until it is complete the app boots into **setup mode** rather than
failing — a missing config is never a crash.

The wizard writes the shared settings into Hermes' own `.env` too, so the Skills
and the app agree on where the vault is.

A clean install deliberately starts with **no Sections, no Templates and no
Pipelines**. Nothing is invented for you.

---

## When something looks empty or missing

| Symptom | Usual cause |
|---|---|
| **Skills list is empty** | The `Hermes-Provisioning/` source is not in the working tree. It fails silently → **[Hermes-Provisioning.md](Hermes-Provisioning.md)** |
| **A note "does not exist" but you can see it** | Windows `MAX_PATH`. Past 260 characters the check returns *false* instead of erroring. Keep vault roots short. |
| **The UI is blank** | The frontend cannot reach the backend — check the API base URL and port, not whether the backend is up. |
| **A capture ran but wrote nothing** | Check whether the source ever produced items before assuming the pipeline failed. |
| **Duplicated notes after a re-run** | The Template is not keyed on a stable `id`. |

---

## Going deeper

| Page | For |
|---|---|
| **[Templates.md](Templates.md)** | Authoring a note type — every key, the access model, testing |
| **[Artifacts.md](Artifacts.md)** | Agent / Skill / Pipeline shapes, disk layout, `.sbf` `.sbb` `.sbd` |
| **[Hermes-Provisioning.md](Hermes-Provisioning.md)** | What depends on the folder held outside the tree |

## Documentation vs memory

Different jobs — they should not duplicate each other:

- **This documentation** — how the framework works and how to use it. Read
  *before* doing something.
- **[`MEMORY.md`](../../MEMORY.md)** — the framework's hard-won rules, written
  *after* something went wrong so it does not go wrong twice.
- **`<app data>/AGENT-MEMORY.md`** — one machine's own paths, vault, mailbox and
  model. Never in this repo.

**Where does a new fact go?** Would it still be true on a fresh install with a
different vault and mailbox? **Yes** → here or `MEMORY.md`. **No** → that
machine's instance memory.
