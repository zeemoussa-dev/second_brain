import { Link, useLocation } from 'react-router';

const VAULT_NAV_ITEMS = [
  { key: 'overview', icon: 'insights', label: 'Overview', href: '/settings/vault' },
  { key: 'entities', icon: 'domain', label: 'Entities', href: '/settings/vault/entities' },
  { key: 'templates', icon: 'description', label: 'Templates', href: '/settings/vault/templates' },
  { key: 'index-filtering', icon: 'filter_alt', label: 'Index Filtering', href: '/settings/vault/index-filtering' },
  { key: 'index-builder', icon: 'auto_stories', label: 'Index Builder', href: '/settings/vault/index-builder' },
  { key: 'export-data', icon: 'ios_share', label: 'Export Data', href: '/settings/vault/export-data' },
] as const;

export function VaultSettingsNav() {
  const { pathname } = useLocation();
  return (
    <nav className="vault-settings-nav">
      {VAULT_NAV_ITEMS.map((item) => (
        <Link
          key={item.key}
          to={item.href}
          className={`vault-settings-nav-item${pathname === item.href ? ' vault-settings-nav-item--active' : ''}`}
        >
          <span className="material-symbols-outlined" aria-hidden="true">{item.icon}</span>
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
