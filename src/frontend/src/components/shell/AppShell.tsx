import { useState } from 'react';
import { Outlet } from 'react-router';
import { Sidebar } from './Sidebar';

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={collapsed ? 'app-shell sidebar-collapsed' : 'app-shell'}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
