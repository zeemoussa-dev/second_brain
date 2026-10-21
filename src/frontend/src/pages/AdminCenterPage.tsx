import { SectionGrid, useVisibleSections } from '../features/settings/SectionGrid';

/** Running the install: who may use it, what it is called, where its
 * data lives, what is deployed onto it, and getting it onto another
 * machine (operator, 2026-10-21 -- fifteen cards on one Settings page
 * had stopped being a menu).
 *
 * Its cards come from the same list Settings reads, filtered on
 * `area`, so the two pages cannot disagree about where a card lives and
 * moving one is a one-word edit in `settingsSections.ts`.
 *
 * **Empty is a real state and says so.** A Power User who reaches this
 * URL has every card filtered out, and an empty grid would read as a
 * broken page. The sidebar does not offer the link to them at all, but
 * the URL is reachable and typing it should explain itself.
 */
export function AdminCenterPage() {
  const sections = useVisibleSections('admin');

  if (sections.length === 0) {
    return (
      <>
        <h1>Admin Center</h1>
        <p className="auth-note" data-testid="admin-center-empty">
          Nothing here is available to your role. Administering this install — users,
          branding, system configuration, plugins and backups — is an Admin's. Ask one
          if you need something changed.
        </p>
      </>
    );
  }

  return (
    <>
      <h1>Admin Center</h1>
      <p className="text-muted">
        Running this install — who may use it, what it is called, what is deployed onto
        it, and moving it to another machine.
      </p>
      <SectionGrid sections={sections} />
    </>
  );
}
