import { useEffect, useState } from 'react';
import { NavLink } from 'react-router';
import { apiFetch } from '../../api/client';

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
        <h2>Second Brain</h2>
      </div>
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
      <NavLink
        to="/my-day"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">☀</span>
        <span className="nav-label">My Day</span>
      </NavLink>
      <NavLink
        to="/settings"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">⚙</span>
        <span className="nav-label">Settings</span>
      </NavLink>
      <NavLink
        to="/system-health"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">⚡</span>
        <span className="nav-label">System Health</span>
      </NavLink>
      <NavLink
        to="/agent-activity"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#128203;</span>
        <span className="nav-label">Agent Activity</span>
      </NavLink>
      <NavLink
        to="/browse"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#128269;</span>
        <span className="nav-label">Browse &amp; Search</span>
      </NavLink>
      <NavLink
        to="/vault"
        className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
      >
        <span className="nav-icon">&#128279;</span>
        <span className="nav-label">The Vault</span>
      </NavLink>
      {!collapsed && version && <div className="sidebar-version">v{version}</div>}
    </nav>
  );
}
