import { Link } from 'react-router';
import { useAuth } from '../auth/AuthGate';
import { SETTINGS_SECTIONS } from './settingsSections';
import type { SettingsSection } from './settingsSections';

/** The card grid Settings and the Admin Center both render.
 *
 * One component rather than two near-identical loops: the pages differ
 * only in which `area` they show and what they say above it, and two
 * copies of a card renderer is how one of them quietly stops matching
 * the other after the next change. */
export function SectionGrid({ sections }: { sections: readonly SettingsSection[] }) {
  return (
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
  );
}

/** The cards of one area that this person may actually open. */
export function useVisibleSections(area: SettingsSection['area']): SettingsSection[] {
  const { may } = useAuth();
  return SETTINGS_SECTIONS.filter(
    (section) => section.area === area && (!section.needs || may(section.needs)),
  );
}

/** Whether the Admin Center has anything in it for this person -- what
 * the sidebar asks before offering the link. Derived from the same list
 * the page renders, so a nav entry can never lead to an empty page, and
 * adding an admin card never needs the sidebar changed as well. */
export function useHasAdminCenter(): boolean {
  return useVisibleSections('admin').length > 0;
}
