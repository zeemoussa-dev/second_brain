/** Every Settings and Admin Center card, in one list.
 *
 * **`area` is what decides which page a card appears on**, so moving one
 * between Settings and the Admin Center is a one-word edit here rather
 * than a cut-and-paste between two files that then drift. The operator
 * asked for the split because fifteen cards on one page had stopped
 * being a menu (2026-10-21).
 *
 *   `admin`    -- running the INSTALL: who may use it, what it is
 *                 called, where its data lives, what is deployed onto
 *                 it, and getting it onto another machine.
 *   `settings` -- shaping the WORK: the vault, the operator's own
 *                 profile, the sections, and what the agents may do.
 *
 * The boundary is "administering the thing" against "configuring the
 * thing", not "Admin-only" against "everyone" -- several `settings`
 * cards are Admin-only too, and `needs` is what controls that.
 *
 * `needs` names the capability required to SEE the card (REQ-SB-101).
 * Hiding is a convenience, never the control: the capability is
 * enforced on the router, so reaching the page by URL still refuses.
 * A card with no `needs` is open to anyone signed in.
 */
export interface SettingsSection {
  key: string;
  icon: string;
  label: string;
  desc: string;
  href: string;
  needs?: string;
  area: 'settings' | 'admin';
}

export const SETTINGS_SECTIONS: readonly SettingsSection[] = [
  { key: 'system', icon: 'tune', label: 'System', desc: 'Core app-level behaviour.', href: '/settings/system', area: 'admin' },
  { key: 'operator', icon: 'badge', label: 'Operator Profile', desc: 'Who your agents act for — your name, your other mail addresses, your timezone, and your team as emails and roles.', href: '/settings/operator', area: 'settings' },
  { key: 'users', icon: 'group', label: 'Users', desc: 'Who can sign in, and what each of them may do. Everyone shares the same vault and agents; a role decides what a person may change.', href: '/settings/users', needs: 'manage_users', area: 'admin' },
  { key: 'branding', icon: 'palette', label: 'Branding', desc: "What this install calls itself, and the logo beside it — in the sidebar, the browser tab and the sign-in screen.", href: '/settings/branding', needs: 'manage_settings', area: 'admin' },
  { key: 'agent-access', icon: 'key', label: 'Agent Access', desc: 'The keys your Hermes workers use to reach this app. Each one is for a single agent, is shown once, and can be revoked.', href: '/settings/agent-access', needs: 'manage_agents', area: 'admin' },
  { key: 'sections', icon: 'hub', label: 'Sections', desc: 'Business-domain groupings agents belong to.', href: '/settings/sections', area: 'settings' },
  { key: 'vault', icon: 'folder_open', label: 'Vault', desc: 'Your Obsidian vault path and status.', href: '/settings/vault', area: 'settings' },
  { key: 'config', icon: 'settings', label: 'Config', desc: 'App configuration.', href: '/settings/config', area: 'admin' },
  { key: 'ui', icon: 'palette', label: 'UI', desc: 'Display and appearance preferences.', href: '/settings/ui', area: 'settings' },
  { key: 'marketplace', icon: 'extension', label: 'Marketplace', desc: 'Install plugins — screens, endpoints and logic for a part of your solution. The framework ships empty.', href: '/settings/marketplace', area: 'admin' },
  { key: 'blueprints', icon: 'dashboard_customize', label: 'Blueprints', desc: 'Pull a ready-made Section — its agents and their skills — onto this install.', href: '/settings/blueprints', area: 'admin' },
  { key: 'artifacts', icon: 'inventory_2', label: 'Artifacts', desc: 'Export or import Skills, Templates, Agents, and Pipelines as a portable bundle.', href: '/settings/artifacts', area: 'admin' },
  { key: 'actions', icon: 'bolt', label: 'Actions', desc: 'The one catalogue of what this app can do — typed inputs, who may call it, and exactly one implementation.', href: '/settings/actions', area: 'settings' },
  { key: 'rules', icon: 'gavel', label: 'Rules', desc: "Checked every time an Action is called, against what it was asked to do — never mail outside the company, never write to that folder.", href: '/settings/rules', needs: 'author_automations', area: 'settings' },
  { key: 'workflows', icon: 'account_tree', label: 'Workflows', desc: 'How a kind of request is handled — the ordered steps, which need your confirmation, and what is reported back.', href: '/settings/workflows', area: 'settings' },
  { key: 'export-data', icon: 'ios_share', label: 'Export Data', desc: 'Browse your real vault and export a chosen slice of notes/files as a portable archive.', href: '/settings/export-data', area: 'admin' },
  { key: 'backup', icon: 'backup', label: 'Backup & Restore', desc: 'Full Hermes structural backup — Agents/Profiles, Cron, Skills — for moving this deployment to a new machine.', href: '/settings/backup', area: 'admin' },
];
