import { Link } from 'react-router';
import { MarketplaceCard } from '../features/settings/MarketplaceCard';

export function SettingsMarketplacePage() {
  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Marketplace</h1>
      <p className="text-muted">
        Plugins add pieces of a solution to this install — their own screens, endpoints and logic.
        The framework itself ships empty. Check a version first: nothing changes until you install it.
      </p>
      <MarketplaceCard />
    </>
  );
}
