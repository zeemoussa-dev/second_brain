# Marketplace

Plugins this framework can install, one folder per published version
(`ADR-022`, `REQ-SB-91`):

```
src/marketplace/<plugin-id>/<version>/
    plugin.json    id, name, version, framework_api, requires
    backend/       the plugin's Python package; __init__.py defines register(api)
    ui/            its screens; index.tsx default-exports routes, nav, settingsPages
```

**Nothing here runs until it is installed** from Settings → Marketplace. The
framework never imports a package from this folder; `scripts/check_plugin_imports.py`
enforces that.

**Packages are published, never hand-edited.** A plugin's source lives in its own
repository; `src/backend/scripts/publish_plugin.py <plugin-repo>` validates it and
places a new version folder here. A published version is never overwritten: a
change is a new version.

`requires` names what must already be present, as Tools or installed plugins.
Alternatives are separated by `|` — `"graph|outlook"` is satisfied by either.
