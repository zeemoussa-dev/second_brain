import { BrowserRouter, Routes, Route } from 'react-router';
import { AppShell } from './components/shell/AppShell';
import { AgentsMapPage } from './pages/AgentsMapPage';
import { CrawlersPage } from './pages/CrawlersPage';
import { MyDayPage } from './pages/MyDayPage';
import { MyDayEmailsPage } from './pages/MyDayEmailsPage';
import { MyDayCalendarPage } from './pages/MyDayCalendarPage';
import { MyDayTodoPage } from './pages/MyDayTodoPage';
import { MyDayApprovalsPage } from './pages/MyDayApprovalsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { AgentActivityPage } from './pages/AgentActivityPage';
import { VaultBrowserPage } from './pages/VaultBrowserPage';
import { VaultGraphPage } from './pages/VaultGraphPage';
import { NoteDetailPage } from './pages/NoteDetailPage';
import { MeetingCockpitPage } from './pages/MeetingCockpitPage';
import { InboxCockpitPage } from './pages/InboxCockpitPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<AgentsMapPage />} />
          <Route path="/crawlers" element={<CrawlersPage />} />
          <Route path="/my-day" element={<MyDayPage />} />
          <Route path="/my-day/emails" element={<MyDayEmailsPage />} />
          <Route path="/my-day/calendar" element={<MyDayCalendarPage />} />
          <Route path="/my-day/todo" element={<MyDayTodoPage />} />
          <Route path="/my-day/approvals" element={<MyDayApprovalsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/system-health" element={<SystemHealthPage />} />
          <Route path="/agent-activity" element={<AgentActivityPage />} />
          <Route path="/browse" element={<VaultBrowserPage />} />
          <Route path="/browse/:stem" element={<NoteDetailPage />} />
          <Route path="/vault" element={<VaultGraphPage />} />
          <Route path="/meeting-cockpit/:stem" element={<MeetingCockpitPage />} />
          <Route path="/inbox-cockpit/:stem" element={<InboxCockpitPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
