import { Link } from 'react-router';

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
  { key: 'sections', icon: 'hub', label: 'Sections', desc: 'Business-domain groupings agents belong to.', href: '/settings/sections' },
  { key: 'vault', icon: 'folder_open', label: 'Vault', desc: 'Your Obsidian vault path and status.', href: '/settings/vault' },
  { key: 'config', icon: 'settings', label: 'Config', desc: 'App configuration.', href: '/settings/config' },
  { key: 'ui', icon: 'palette', label: 'UI', desc: 'Display and appearance preferences.', href: '/settings/ui' },
] as const;

export function SettingsPage() {
  return (
    <>
      <h1>Settings</h1>
      <p className="text-muted">Pick a section to configure.</p>
      <div className="settings-grid">
        {SETTINGS_SECTIONS.map((section) => (
          <Link key={section.key} className="card settings-card" to={section.href}>
            <span className="material-symbols-outlined settings-card-icon" aria-hidden="true">
              {section.icon}
            </span>
            <h2 className="settings-card-title">{section.label}</h2>
            <p className="settings-card-desc">{section.desc}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
