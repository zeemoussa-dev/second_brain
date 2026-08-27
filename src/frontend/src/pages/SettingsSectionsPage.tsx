import { Link } from 'react-router';
import { SectionsCard } from '../features/settings/SectionsCard';

export function SettingsSectionsPage() {
  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Sections</h1>
      <SectionsCard />
    </>
  );
}
