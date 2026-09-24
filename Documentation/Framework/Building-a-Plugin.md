# Building a Plugin

A **plugin** adds a piece of a solution to an install: its own screens,
endpoints, Templates and logic. The framework ships **empty** — My Day is a
screen, Customers and Partners are one business's model, and a second brain built
for a CFO should carry neither (`ADR-021`, `ADR-022`).

Build a plugin when the thing you are adding is **not true of every install**.
Build a [Skill](Building-a-Skill.md) when an agent needs a new capability, and a
[Template](Templates.md) when you only need a new kind of note.

---

## The shape of a plugin

Plugin source lives in its **own repository** (`sb-plugins-my-day`,
`sb-plugins-entities`). A validated, versioned copy is published into the
framework's Marketplace and installed from Settings.

```
plugin.json                  id, name, version, framework_api, requires
backend/__init__.py          register(api) -- mounted under /plugins/<id>/
backend/*.py                 its own modules, relative imports
ui/index.tsx                 default-exports the screens contract
ui/*.tsx, *.ts, *.css        its screens
templates/<id>/Template.json its Templates
tests/                       its own tests: run on publish, never packaged
```

`plugin.json`:

```json
{
  "id": "my-day",
  "name": "My Day",
  "description": "Your day at a glance.",
  "version": "1.3.0",
  "framework_api": 4,
  "requires": ["graph|outlook"]
}
```

- **`id`** becomes a folder name, a package name and a URL segment: lowercase
  letters, digits and hyphens.
- **`framework_api`** must match the host **exactly**. A plugin is never loaded
  by a framework with a different API version, so it can never half-work; every
  installed plugin is republished when that version moves.
- **`requires`** names Tools or other plugins; `"graph|outlook"` is met by either.

---

## The backend: `register(api)`

The plugin's backend package defines one entry point. Everything it may do to or
with the framework arrives through `api` — a facade of plain dicts, lists and
tuples, never a framework entity class:

```python
def register(api) -> None:
    api.register_seed_data_file("Settings/Entities.md")
    api.register_people_folders(["Work/Customers", "Work/Partners"])

    customers = Customers(api)
    api.provide_service("entities.customers", customers)
    api.register_subject_enricher(customers.subject_enricher)
    api.register_agent_matcher(CockpitAgentMatcher(api).match)

    api.register_router(build_router(EntitiesRegistry(api)))
```

### What the API offers (v4)

| Call | What it gives you |
|---|---|
| `api.vault.index()` | Every indexed note by stem: `path`, `stem`, `frontmatter`, `tags`, wikilinks |
| `api.vault.notes_in_kind(kind)` | Paths of the notes in one `Work/<kind>/` folder |
| `api.vault.read_note(path)` | `(frontmatter, body)` |
| `api.pipelines.get(id)` | `id`, `name`, `cron_job_id`, `cron_profile_id`, or None |
| `api.hermes.run_cron_job(job, profile)` | Fires a cron job now; returns when the trigger is sent |
| `api.agents.list_experts()` | Expert agents: `id`, `name`, `description`, `section_id` |
| `api.sections.get(id)` | `id`, `name`, `fallback_agent_id` |
| `api.data.read_text(path)` / `write_text(path, text)` | This plugin's own registered data files, nothing else |
| `api.register_router(router)` | Mounted under `/plugins/<id>/` |
| `api.register_subject_enricher(fn)` | Fills a field a note does not carry, for Cockpit |
| `api.register_agent_matcher(fn)` | Which Experts fit a conversation, and who answers when nobody does |
| `api.register_people_folders([...])` | Vault folders whose `**/People/` holds Person notes |
| `api.register_seed_data_file(path)` | A settings file the plugin's Skills need; carried empty by `.sbf` |
| `api.provide_service(name, obj)` / `api.get_service(name)` | One plugin uses another without importing it |

Rules the host enforces:

- **The backend may import `app.plugin_api` and nothing else** from the
  framework. Its own modules import each other relatively.
- **A plugin that fails is isolated.** A `register` that raises disables that
  plugin, records the reason in System Health, and leaves every other plugin
  loaded. Nothing it registered before raising is kept.
- **A service name must start with the plugin's own id** (`entities.customers`).
- **Ask for a service when you need it, not in `register`.** Plugins load in
  install order, so the provider may load after you. `get_service` returns None
  when that plugin is not installed — handle that as a normal state.
- **Enrichers and matchers are advisory**: an enricher never overrides a value
  the note already has, returned agent ids that are not registered are ignored,
  and one that raises is skipped.

---

## The screens

`ui/index.tsx` default-exports what the plugin contributes:

```tsx
const ui: PluginUi = {
  routes: [{ path: '/my-day', component: DayPage }],
  nav: [{ to: '/my-day', label: 'My Day', icon: '☀' }],
  settingsPages: [{ path: '', label: 'Entities', component: EntitiesPage }],
  cockpitInfoFields: [{ subjectKind: 'email', label: 'Customer', key: 'customer' }],
  cockpitTabs: [{ subjectKind: 'email', id: 'emails', label: 'Emails', icon: '✉', component: EmailsTab }],
};
export default ui;
```

- Routes and nav targets must sit under `/<plugin-id>`; settings pages mount at
  `/settings/plugins/<plugin-id>`. A contribution that breaks the rule is skipped
  and reported on System Health rather than silently mounted.
- Cockpit info fields are appended after the Cockpit's own rows; a key already
  shown is left out, so a field never appears twice.
- **Cockpit tabs** (v3) are appended after the Cockpit's own tabs, for one
  `subjectKind`. The tab's screen is given `{ subjectKind, subjectNoteStem }` and
  owns everything inside it. This is how a plugin adds a view the Cockpit itself
  must not have: the Cockpit is a generic component for chatting with agents
  about a subject, and what an email or a meeting IS belongs to the plugin that
  understands it. A Thread's own emails is My Day's tab.
- **Screens may import only their own files, `src/pluginHost/`, and react /
  react-router.** `pluginHost/api` gives `apiFetch`; `pluginHost/types` gives the
  contract. Importing a framework feature is refused at publish time — it would
  break the next time that feature changed.
- **Rendering vault text is the host's job** (v4). `pluginHost/noteText` exports
  `NoteText` -- markdown, real `[[wikilinks]]`, and ```mermaid fences drawn as
  diagrams -- and `MermaidDiagram` for a screen holding diagram source rather
  than a note. The framework's own screens render through the same component, so
  a plugin cannot drift from how the app draws the same file. Writing your own
  markdown or mermaid renderer is the mistake this replaces; `mermaid` itself
  stays a host library and a screen importing it is refused.
- Global CSS classes (`card`, `item-row`, `btn`, `field-labeled`) are the host's
  and are fine to use; a plugin's own styles ship in its `ui/`.

Screens are composed at **build time**: installing copies them into the
frontend's `src/plugins/<id>/` and the app is rebuilt with them.

---

## Templates

A package's `templates/<id>/Template.json` is installed by the Marketplace —
**only when the install has no Template with that id**. An existing one is
adopted as it is, never overwritten: it may carry the operator's own edits. The
plugin's ownership entry records which Templates it brought, and uninstalling
leaves them in place, because notes written against them stay in the vault.

---

## Publishing

One script validates a plugin repository and publishes one version into the
framework's Marketplace:

```bash
src/backend/.venv/Scripts/python.exe src/backend/scripts/publish_plugin.py <plugin-repo> [--dry-run]
```

Every check runs before anything is written:

1. **Manifest** — valid id, `x.y.z` version, the framework API this framework provides.
2. **Layout** — `backend/__init__.py`, `ui/index.tsx` and/or `templates/<id>/Template.json`.
3. **Import boundary** — the backend imports only `app.plugin_api`; the screens
   import only their own files, `src/pluginHost/` and the host's libraries.
4. **The plugin's own tests** (`tests/`, with the framework on `PYTHONPATH`).
5. **The screens build inside this framework** — a real `npm run build` with the
   screens copied in at an installed plugin's depth.
6. **Version** — a published version is never overwritten. Bump it.

A refusal lists every problem and publishes nothing. Tests are never packaged.

---

## Installing

Settings → Marketplace lists published plugins with their versions and
compatibility. **Check** a version first: it reports what installing would do —
which Templates it adds, which it keeps, what it replaces — and changes nothing.

### From the plugin's own repository

A plugin does not have to be published here at all (`ADR-024`). Settings →
Marketplace → **Install from a repository** takes a git URL and a branch, tag or
commit — or a folder on this machine while you are writing one. The repository is
cloned to a temporary folder, checked, installed, and the clone is discarded.

Three gates run, the same ones publishing applies: the `framework_api` match, the
import boundary, and that the screens build inside this framework. The plugin's own
tests stay with publishing — installing must not need your test dependencies.

What is installed remembers where it came from — repository, ref and the resolved
commit — and the page shows it. **Update** pulls that same source again, which is how
a plugin tracked from a branch is upgraded: the code moves while the version string
stays put, so there is deliberately no "already installed" refusal for a source.
A plugin installed from this framework's Marketplace records no source and says so
when asked to update; install another published version instead, or install it once
from its repository to track that from then on.

This is what an agent install uses: its repository is not the framework's, and it is
not allowed to commit a package here (`ADR-023`).

Install copies the backend into the install's config folder
(`<app data>/plugins/<id>/`), the screens into the frontend's
`src/plugins/<id>/`, records what it owns, and reports **restart required**: a
plugin's backend is loaded at startup. Screens appear as soon as the frontend
picks them up.

Replacing a version never destroys the installed one first: the package is staged
beside it, the installed pieces are moved aside whole, the new ones moved in, and
only then is the old version deleted. A failure before the swap completes puts
everything back and says why (`BUG-065`).

Uninstall removes exactly what the ownership record lists, never a path outside
the two plugin folders, and leaves Templates and vault notes alone.

---

## Working on a plugin

A sensible loop:

1. Write the backend and its tests; run them with the framework on `PYTHONPATH`:
   `PYTHONPATH=<second-brain>/src/backend python -m pytest tests`.
2. `publish_plugin.py <repo> --dry-run` — every gate, nothing written.
3. Publish, install from Settings → Marketplace, restart the backend.
4. Check System Health: the plugin should read `loaded`, with its route prefix.
   A `refused` or `disabled` row carries the reason.

**Before removing something from the framework in favour of a plugin**, compare
them on real data first: run both and diff the answers. That is how the My Day
and Entities extractions were done — endpoints, Cockpit views and resolved
customers compared note by note before the framework copy was deleted.

---

## Traps

| Trap | What actually happens |
|---|---|
| Bumping `FRAMEWORK_API` | Every installed plugin built for the old value is **refused** until republished. System Health says so. |
| Calling `get_service` inside `register` | The provider may not have loaded yet. Ask at call time. |
| A screen importing a framework feature | Publishing refuses it. Ask for a host contract addition instead. |
| Expecting an install to update a Template | It never overwrites one. Adopt, or ship a new id. |
| Editing an installed plugin in place | The Marketplace owns those folders; edit the repository, then publish a new version or install from the repository again. |
| Expecting Update on a Marketplace-installed plugin | It has no repository to pull. Install it once from its repository to track that instead. |
| Forgetting the restart | Screens appear immediately, endpoints do not. |

---

## Related

- [Artifacts.md](Artifacts.md) — plugin packages beside the other artifacts
- [Building-a-Skill.md](Building-a-Skill.md) — agent capabilities, which plugins do not carry
- [Templates.md](Templates.md) — the note types a plugin may ship
- `Implementation/Architecture/ADR.md` — `ADR-021` (the framework ships empty), `ADR-022` (the plugin host)
