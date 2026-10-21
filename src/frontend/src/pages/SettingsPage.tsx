import { Link } from 'react-router';
import { SectionGrid, useHasAdminCenter, useVisibleSections } from '../features/settings/SectionGrid';
import { pluginSettingsPages } from '../pluginHost/registry';

// Icon-card grid landing page (operator, 2026-08-27: "I need a Settings
// Landing Page with Cards to each Section... I want Icons per Section
// and a Grid Look not a row"). Replaces the old flat SectionsCard
// stack -- it now lives on its own drill-down page, reachable by
// clicking its card here, same flat-sibling-route shape My Day's own
// landing grid already established. The "Providers" card was removed
// 2026-08-28 (operator: the whole Providers UI/router was already dead
// -- no backend route existed) -- Provider stays a real backend entity
// (business/core/provider/), just with no Settings UI of its own yet.
//
// Split in two on 2026-10-21 (operator: "The Settings is now too many
// Make an Admin Center Separate for Admin Stuff"). The cards live in
// features/settings/settingsSections.ts with an `area`; this page shows
// the ones about shaping the WORK, the Admin Center the ones about
// running the INSTALL.
export function SettingsPage() {
  const sections = useVisibleSections('settings');
  const hasAdminCenter = useHasAdminCenter();

  return (
    <>
      <h1>Settings</h1>
      <p className="text-muted">
        How this app works on your knowledge — your vault, your profile, and what your
        agents may do.
      </p>
      <SectionGrid sections={sections} />

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

      {/* A pointer, not a duplicate: someone who came here looking for
          Users or Backup should be told where those went rather than
          concluding they were removed. Only shown to a person who has
          something there. */}
      {hasAdminCenter && (
        <p className="auth-note" style={{ marginTop: 'var(--space-5)' }}>
          Running the install — users, branding, plugins, backups — is in the{' '}
          <Link to="/admin">Admin Center</Link>.
        </p>
      )}
    </>
  );
}
