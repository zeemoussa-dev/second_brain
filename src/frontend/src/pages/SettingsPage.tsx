import { Link } from 'react-router';
import { useAuth } from '../features/auth/AuthGate';
import { pluginSettingsPages } from '../pluginHost/registry';

// Icon-card grid landing page (operator, 2026-08-27: "I need a Settings
// Landing Page with Cards to each Section... I want Icons per Section
// and a Grid Look not a row"). Replaces the old flat SectionsCard
// stack — it now lives on its own drill-down page, reachable by
// clicking its card here, same flat-sibling-route shape My Day's own
// landing grid already established. The "Providers" card was removed
// 2026-08-28 (operator: the whole Providers UI/router was already dead
// -- no backend route existed) -- Provider stays a real backend entity
// (business/core/provider/), just with no Settings UI of its own yet.
const SETTINGS_SECTIONS = [
  { key: 'system', icon: 'tune', label: 'System', desc: 'Core app-level behaviour.', href: '/settings/system' },
  { key: 'operator', icon: 'badge', label: 'Operator Profile', desc: 'Who your agents act for — your name, your other mail addresses, your timezone, and your team as emails and roles.', href: '/settings/operator' },
  { key: 'users', icon: 'group', label: 'Users', desc: 'Who can sign in, and what each of them may do. Everyone shares the same vault and agents; a role decides what a person may change.', href: '/settings/users', needs: 'manage_users' },
  { key: 'sections', icon: 'hub', label: 'Sections', desc: 'Business-domain groupings agents belong to.', href: '/settings/sections' },
  { key: 'vault', icon: 'folder_open', label: 'Vault', desc: 'Your Obsidian vault path and status.', href: '/settings/vault' },
  { key: 'config', icon: 'settings', label: 'Config', desc: 'App configuration.', href: '/settings/config' },
  { key: 'ui', icon: 'palette', label: 'UI', desc: 'Display and appearance preferences.', href: '/settings/ui' },
  { key: 'marketplace', icon: 'extension', label: 'Marketplace', desc: 'Install plugins — screens, endpoints and logic for a part of your solution. The framework ships empty.', href: '/settings/marketplace' },
  { key: 'blueprints', icon: 'dashboard_customize', label: 'Blueprints', desc: 'Pull a ready-made Section — its agents and their skills — onto this install.', href: '/settings/blueprints' },
  { key: 'artifacts', icon: 'inventory_2', label: 'Artifacts', desc: 'Export or import Skills, Templates, Agents, and Pipelines as a portable bundle.', href: '/settings/artifacts' },
  { key: 'actions', icon: 'bolt', label: 'Actions', desc: 'The one catalogue of what this app can do — typed inputs, who may call it, and exactly one implementation.', href: '/settings/actions' },
  { key: 'workflows', icon: 'account_tree', label: 'Workflows', desc: 'How a kind of request is handled — the ordered steps, which need your confirmation, and what is reported back.', href: '/settings/workflows' },
  { key: 'export-data', icon: 'ios_share', label: 'Export Data', desc: 'Browse your real vault and export a chosen slice of notes/files as a portable archive.', href: '/settings/export-data' },
  { key: 'backup', icon: 'backup', label: 'Backup & Restore', desc: 'Full Hermes structural backup — Agents/Profiles, Cron, Skills — for moving this deployment to a new machine.', href: '/settings/backup' },
] as const;

export function SettingsPage() {
  // REQ-SB-101: a card whose `needs` the signed-in person does not have
  // is not offered. This is a convenience, never the control -- the
  // capability is enforced on the router, so reaching the page by URL
  // still refuses. Hiding it only spares someone a 403 they cannot act
  // on; every card without a `needs` is open to anyone signed in.
  const { may } = useAuth();
  const sections = SETTINGS_SECTIONS.filter((section) => !section.needs || may(section.needs));
  return (
    <>
      <h1>Settings</h1>
      <p className="text-muted">Pick a section to configure.</p>
      <div className="settings-grid">
        {sections.map((section) => (
          <Link key={section.key} className="card settings-card" to={section.href}>
            <span className="material-symbols-outlined settings-card-icon" aria-hidden="true">
              {section.icon}
            </span>
            <h2 className="settings-card-title">{section.label}</h2>
            <p className="settings-card-desc">{section.desc}</p>
          </Link>
        ))}
      </div>
      {/* Settings pages contributed by installed plugins (ADR-022). Absent
          entirely when no installed plugin has any. */}
      {pluginSettingsPages.length > 0 && (
        <>
          <h2 style={{ marginTop: 'var(--space-4)' }}>Plugins</h2>
          <div className="settings-grid">
            {pluginSettingsPages.map((page) => (
              <Link key={page.path} className="card settings-card" to={page.path}>
                <span className="material-symbols-outlined settings-card-icon" aria-hidden="true">
                  extension
                </span>
                <h2 className="settings-card-title">{page.label}</h2>
                <p className="settings-card-desc">From the {page.pluginId} plugin.</p>
              </Link>
            ))}
          </div>
        </>
      )}
    </>
  );
}
