import { NavLink } from 'react-router';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
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
    </nav>
  );
}
