import { Link } from 'react-router';
import { BlueprintsCard } from '../features/settings/BlueprintsCard';

export function SettingsBlueprintsPage() {
  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Blueprints</h1>
      <p className="text-muted">
        A blueprint is a recipe for a Section — its agents, and the skills each one needs.
        Check it first: nothing is created until every template it depends on is present.
      </p>
      <BlueprintsCard />
    </>
  );
}
