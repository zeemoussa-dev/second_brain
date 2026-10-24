import { useEffect, useState } from 'react';
import { NavLink } from 'react-router';
import { apiFetch } from '../../api/client';
import { pluginNavEntries } from '../../pluginHost/registry';
import { SignedInAs } from './SignedInAs';
import { useBranding } from '../../features/branding/BrandingProvider';
import { useHasAdminCenter } from '../../features/settings/SectionGrid';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

// Version stamp (2026-09-03, operator: "I want to have the current
// version number in the UI") -- reads GET /health's own `version` field
// (app/version.py, the repo-root VERSION file). Always in the sidebar
// (not buried in a Settings sub-page) so it's visible from anywhere in
// the app. Silently blank on a fetch failure -- a missing version
// string is never worth a visible error in the nav itself.
function useAppVersion(): string | null {
  const [version, setVersion] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    apiFetch<{ status: string; version?: string }>('/health')
      .then((res) => {
        if (!cancelled) setVersion(res.version ?? null);
      })
      .catch(() => {
        if (!cancelled) setVersion(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return version;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const version = useAppVersion();
  const { app_name: appName, logoUrl } = useBranding();
  // Asked of the same list the page renders, so the link can never
  // lead to a page with nothing on it.
  const hasAdminCenter = useHasAdminCenter();
  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <button
          type="button"
          className="burger-btn"
          aria-label="Toggle navigation"
          aria-expanded={!collapsed}
          onClick={onToggle}
        >
          ☰
        </button>
        {logoUrl && <img className="sidebar-logo" src={logoUrl} alt="" />}
        <h2 title={appName}>{appName}</h2>
      </div>
      <div className="sidebar-links">
      <NavLink
        to="/"
        end
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">◎</span>
        <span className="nav-label">Agents Map</span>
      </NavLink>
      <NavLink
        to="/chat"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#128172;</span>
        <span className="nav-label">Chat</span>
      </NavLink>
      <NavLink
        to="/crawlers"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#128375;</span>
        <span className="nav-label">Crawlers</span>
      </NavLink>
      {/* Installed plugins' entries (ADR-022) sit where My Day sat before it
          became a plugin, so extracting it does not move it in the sidebar. */}
      {pluginNavEntries.map((entry) => (
        <NavLink
          key={entry.to}
          to={entry.to}
          className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
        >
          <span className="nav-icon">{entry.icon ?? '◆'}</span>
          <span className="nav-label">{entry.label}</span>
        </NavLink>
      ))}
      {/* REQ-SB-103 -- a Workflow that stopped to ask holds until
          somebody answers, so there has to be somewhere that shows it
          is waiting. Above System Health because it is work of yours,
          not a reading about the machine. */}
      <NavLink
        to="/waiting-on-me"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#9203;</span>
        <span className="nav-label">Waiting on You</span>
      </NavLink>
      <NavLink
        to="/system-health"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">⚡</span>
        <span className="nav-label">System Health</span>
      </NavLink>
      <NavLink
        to="/flow"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#128506;</span>
        <span className="nav-label">The Flow</span>
      </NavLink>
      <NavLink
        to="/agent-activity"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#128203;</span>
        <span className="nav-label">Agent Activity</span>
      </NavLink>
      {/* One entry, because they are one screen now (operator, 2026-10-24:
          "Need to Merge the Vault with the Search"). Search, the note list and
          the knowledge graph were three ways of reading one vault behind two
          nav items that each claimed to be the vault. */}
      <NavLink
        to="/browse"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#128279;</span>
        <span className="nav-label">The Vault</span>
      </NavLink>
      </div>
      {/* REQ-SB-101 -- who is signed in, then the version, at the foot of
          the panel. The user sits ABOVE the version because it is the line
          someone actually comes here to read; the version stays the last
          thing, where it has always been. */}
      {/* Configuration and the person using the app live together at the
          foot (operator, 2026-10-21). They are the two things you reach
          for about the app ITSELF rather than about your work, so they
          sit below the scrolling list of places to go rather than
          inside it. */}
      <div className="sidebar-foot">
        <NavLink
          to="/settings"
          className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
        >
          <span className="nav-icon">⚙</span>
          <span className="nav-label">Settings</span>
        </NavLink>
        {hasAdminCenter && (
          <NavLink
            to="/admin"
            className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
          >
            <span className="nav-icon">&#128737;</span>
            <span className="nav-label">Admin Center</span>
          </NavLink>
        )}
        <SignedInAs collapsed={collapsed} />
        {!collapsed && version && <div className="sidebar-version">v{version}</div>}
      </div>
    </nav>
  );
}
