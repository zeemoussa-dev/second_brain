import { SectionsCard } from '../features/settings/SectionsCard';
import { ProvidersCard } from '../features/settings/ProvidersCard';

export function SettingsPage() {
  return (
    <>
      <h1>Settings</h1>
      <p className="text-muted">
        Vault and Connections content is not built yet — this page is
        reachable from the sidebar, per REQ-SB-12's acceptance criteria.
      </p>
      <SectionsCard />
      <ProvidersCard />
    </>
  );
}
