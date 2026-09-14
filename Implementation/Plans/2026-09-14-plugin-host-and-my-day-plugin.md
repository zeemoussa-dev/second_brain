# Plugin host + the My Day plugin — extraction plan

**Date:** 2026-09-14
**Decided in:** `ADR-022` (plugins carry code; the framework is a plugin host with a
Marketplace), building on `ADR-021` (the repository split).
**Requirement:** `REQ-SB-91`. **Related:** `BUG-062`, `BUG-063`.

## Goal

The framework hosts code-carrying plugins, and My Day leaves the framework as the first
one, with no loss of behaviour.

"Done" means:
- the framework boots and passes its tests with **no plugins installed**, and
- with the My Day plugin installed from the Marketplace, every My Day screen and endpoint
  behaves as it does today.

## What My Day is today

Verified against the code on 2026-09-14.

| Layer | Files | Size |
|---|---|---|
| Business logic | `backend/app/business/my_day.py` | 342 lines |
| Day-window validation | `backend/app/business/logic/my_day_window.py` | 30 lines |
| HTTP | `backend/app/api/my_day_router.py` | 5 endpoints: `/summary`, `/emails`, `/calendar`, `/todo`, `/refresh` |
| API client | `frontend/src/features/my-day/client.ts` | 59 lines |
| Screens | `MyDayPage`, `MyDayEmailsPage`, `MyDayCalendarPage`, `MyDayTodoPage`, `MyDayApprovalsPage` | 620 lines |

Each piece is mounted by hand:
- `main.py` calls `app.include_router(my_day_router)`
- `App.tsx` declares five hardcoded `/my-day/*` routes
- `Sidebar.tsx` hardcodes a `<NavLink to="/my-day">`

## Framework internals My Day reaches → Plugin API v1

My Day uses exactly five framework capabilities. Together they form the first version of
the facade (`app.plugin_api`); nothing else is exposed until another plugin needs it.

| Today (direct internal import) | Plugin API v1 |
|---|---|
| `VaultManager().get_index()` | `vault.index()` |
| `vault_writer.list_notes_in_kind_folder(kind)` | `vault.notes_in_kind(kind)` |
| `vault_writer.read_note(path)` | `vault.read_note(path)` |
| `PipelineManager().get_by_id(id)` | `pipelines.get(id)` |
| `get_client().cli.run_cron_job(name)` | `hermes.run_cron_job(name)` |

Registration surface, also part of v1:
- `register_router(router)`, mounted at `/plugins/<id>/`
- screens, nav entries and Settings pages, supplied by the frontend half of the plugin
- `register_subject_enricher(fn)`, the Cockpit seam below

## Seams to cut before My Day can leave

Cockpit is **framework** (operator: *"Cockpit is a Concept of Having Multiple Agents
Communicate with each other"*). My Day uses it. Two places in core point at My Day, and
core must never point at a plugin.

1. **Customer resolution.** `business/logic/cockpit_view.py` imports `my_day` for one thing:
   `customer_from_tags(...)` and `customer_name_by_tag()`, which resolve a subject's customer
   from `customer/<slug>` tags. That is Entities logic, not My Day logic.
   - **Seam:** Cockpit exposes a subject-enricher registry and applies every registered
     enricher when it composes a view.
   - The My Day plugin registers the customer resolver for now, so behaviour is identical.
   - The resolver moves to the Entities plugin (`sb-plugins-entities`) when that extraction happens.
2. **Back links.** `InboxCockpitPage` links to `/my-day/emails`, and `MeetingCockpitPage`
   links to `/my-day/calendar`.
   - **Seam:** the screen that opens a Cockpit passes `state={{ backTo, backLabel }}`, and
     Cockpit renders the back link from that state, or no link when there is none.
   - My Day's own links into Cockpit (`/inbox-cockpit/:stem`, `/meeting-cockpit/:stem`)
     already point plugin → framework, which is the allowed direction.
3. **`my_day_window.py`** is imported only by `my_day_router`, so it moves with the plugin.

Cockpit carries its own business leak: `moderator.py` picks a "customer expert" agent
through a hardcoded Customer Section. It is not needed for My Day and is logged as
`BUG-063`, resolved with the Entities plugin through a matcher hook.

## Phases

Each phase ends runnable, tested and committed on its own.

### Phase 1 — Backend plugin host
- **Manifest schema** (`plugin.json`): `id`, `name`, `version`, `framework_api` (major
  version), `requires` (Tools or other plugins), and entry points for backend, UI and
  Hermes content.
- **Installed plugins** are unpacked into the install's config folder, at
  `<SECOND_BRAIN_DATA_PATH>/plugins/<id>/`, with an ownership record in
  `plugins/installed.json`. An agent repository pins which plugins, at which versions.
- **Loader.** Runs in the FastAPI lifespan and does four things, in order:
  - reads `installed.json`;
  - refuses any plugin whose `framework_api` major differs from the host's;
  - imports each plugin's backend and calls its `register(api)`;
  - mounts its routers under `/plugins/<id>/`.

  A plugin that raises is disabled and recorded; the app still boots.
- **`app/plugin_api.py`**, the facade v1 from the table above.
- **Import check** (a script, also used at publish time): a plugin may import only
  `app.plugin_api`, and core may import nothing from `marketplace/` or any plugin.
- **System Health** gains a `plugins` section listing installed, loaded, refused (with
  the reason) and disabled (with the error).

### Phase 2 — Frontend plugin host (build-time composition)
- **Route registry and nav registry.** Plugin routes are added to `App.tsx` from the
  registry, and plugin nav entries to `Sidebar.tsx`. The framework's own routes stay as they
  are.
- **Composition.** `import.meta.glob('./plugins/*/index.tsx', { eager: true })`.
  - Installing copies a plugin's `ui/` into `src/frontend/src/plugins/<id>/`, which is
    gitignored and generated.
  - Each plugin's `index.tsx` exports `{ routes, nav, settingsPages }`.
- **Rebuild on install**, using the Node already shipped in `tools/node`.

### Phase 3 — Cockpit seams
- Add the subject-enricher registry to Cockpit's view composition.
- Add back-link state to both Cockpit screens.
- Core no longer imports `my_day` from Cockpit. Verified by the import check.

### Phase 4 — Marketplace
- **Package format**: `plugin.json`, `backend/` (Python package), `ui/` (screen source),
  `hermes/` (Skills, agents, pipelines, i.e. today's Blueprint layer) and `templates/`.
- **Publish** runs from the plugin repository and validates four things before placing a
  versioned package in the framework's `marketplace/<id>/<version>/`:
  - the import check passes;
  - `framework_api` fits the host;
  - the plugin's tests pass;
  - the UI type-checks and builds.
- **Settings → Marketplace**, grown out of the Blueprints page: list, preflight, install,
  uninstall.
  - Uninstall removes what the ownership record lists.
  - Notes the plugin wrote into the vault stay in the vault.

### Phase 5 — Extract My Day
1. Create the plugin repository, `sb-plugins-my-day`.
2. Port the backend onto Plugin API v1, with no internal imports. The routes keep their
   shape under `/plugins/my-day/`, and the client's base path changes to match.
3. Register the customer enricher (seam 1) and pass back-link state from My Day's links
   (seam 2).
4. Publish it to the Marketplace, then install it on this machine.
5. **Parity check** before removing anything from the framework:
   - all five endpoints return the same data for the same `day`;
   - all five screens render;
   - Refresh still triggers the `threads-builder` / `meeting-builder` cron jobs;
   - both Cockpits open from My Day and link back.
6. Remove My Day from the framework behind the same dependency gate used for the
   `ADR-021` move.
7. Confirm the framework boots and passes its tests with the plugin **uninstalled**.

## Gates

- **Core purity:** the framework imports nothing from `marketplace/` or any plugin.
- **Plugin boundary:** a plugin imports only `app.plugin_api`.
- **Version:** a mismatched `framework_api` is refused, never half-loaded.
- **Parity** is established before any removal.
- **Empty boot:** no plugins installed → the app boots and all framework tests pass.

## Follow-ups (not in this plan)

- **Entities plugin:** `Entities.md`, the `customer` / `partner` / `opportunity` Templates,
  the company Skills, `company_index`, and the Settings Entities page. This resolves
  `BUG-062`, and `BUG-063` through a matcher hook.
- **Restore the `outlook` Tool** beside `graph`, from `6c7bfbb^`.
