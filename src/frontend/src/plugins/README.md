# Installed plugin screens — generated, do not edit

Every folder here is the `ui/` of one installed plugin, copied in by the
Marketplace when the plugin is installed (`ADR-022`, `REQ-SB-91`). The app is
then rebuilt, and `src/pluginHost/registry.ts` picks each one up through
`import.meta.glob('../plugins/*/index.tsx')`.

This folder is gitignored: the framework repository never contains a plugin's
screens. A plugin's source lives in its own repository.

Each `<plugin-id>/index.tsx` default-exports what the plugin contributes:

- `routes` — screens, every path under `/<plugin-id>`
- `nav` — sidebar entries, every target under `/<plugin-id>`
- `settingsPages` — Settings pages, mounted under `/settings/plugins/<plugin-id>`
- `cockpitInfoFields` — rows added to a Cockpit's info panel for `email` or `meeting` subjects, after the Cockpit's own rows; a key already shown is skipped

A contribution that breaks these rules is skipped and reported, never mounted.
