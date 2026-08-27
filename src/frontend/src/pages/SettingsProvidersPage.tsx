import { Link } from 'react-router';
import { ProvidersCard } from '../features/settings/ProvidersCard';

export function SettingsProvidersPage() {
  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Providers</h1>
      <ProvidersCard />
    </>
  );
}
