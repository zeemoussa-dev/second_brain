import { BrowserRouter, Routes, Route } from 'react-router';
import { AppShell } from './components/shell/AppShell';
import { SetupPage } from './pages/SetupPage';
import { AgentsMapPage } from './pages/AgentsMapPage';
import { ChatPage } from './pages/ChatPage';
import { CrawlersPage } from './pages/CrawlersPage';
import { MyDayPage } from './pages/MyDayPage';
import { MyDayEmailsPage } from './pages/MyDayEmailsPage';
import { MyDayCalendarPage } from './pages/MyDayCalendarPage';
import { MyDayTodoPage } from './pages/MyDayTodoPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SettingsArtifactsPage } from './pages/SettingsArtifactsPage';
import { SettingsBlueprintsPage } from './pages/SettingsBlueprintsPage';
import { SettingsMarketplacePage } from './pages/SettingsMarketplacePage';
import { SettingsSystemPage } from './pages/SettingsSystemPage';
import { SettingsSectionsPage } from './pages/SettingsSectionsPage';
import { SettingsVaultPage } from './pages/SettingsVaultPage';
import { SettingsVaultEntitiesPage } from './pages/SettingsVaultEntitiesPage';
import { SettingsVaultTemplatesPage } from './pages/SettingsVaultTemplatesPage';
import { SettingsVaultIndexBuilderPage } from './pages/SettingsVaultIndexBuilderPage';
import { SettingsVaultIndexFilteringPage } from './pages/SettingsVaultIndexFilteringPage';
import { SettingsExportDataPage } from './pages/SettingsExportDataPage';
import { SettingsBackupPage } from './pages/SettingsBackupPage';
import { SettingsConfigPage } from './pages/SettingsConfigPage';
import { SettingsUIPage } from './pages/SettingsUIPage';
import { SystemHealthPage } from './pages/SystemHealthPage';
import { AgentActivityPage } from './pages/AgentActivityPage';
import { VaultBrowserPage } from './pages/VaultBrowserPage';
import { VaultGraphPage } from './pages/VaultGraphPage';
import { NoteDetailPage } from './pages/NoteDetailPage';
import { MeetingCockpitPage } from './pages/MeetingCockpitPage';
import { InboxCockpitPage } from './pages/InboxCockpitPage';
import { pluginRoutes, pluginSettingsPages } from './pluginHost/registry';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<AgentsMapPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/crawlers" element={<CrawlersPage />} />
          <Route path="/my-day" element={<MyDayPage />} />
          <Route path="/my-day/emails" element={<MyDayEmailsPage />} />
          <Route path="/my-day/calendar" element={<MyDayCalendarPage />} />
          <Route path="/my-day/todo" element={<MyDayTodoPage />} />
          <Route path="/approvals" element={<ApprovalsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/settings/system" element={<SettingsSystemPage />} />
          <Route path="/settings/sections" element={<SettingsSectionsPage />} />
          <Route path="/settings/vault" element={<SettingsVaultPage />} />
          <Route path="/settings/vault/entities" element={<SettingsVaultEntitiesPage />} />
          <Route path="/settings/vault/templates" element={<SettingsVaultTemplatesPage />} />
          <Route path="/settings/vault/index-filtering" element={<SettingsVaultIndexFilteringPage />} />
          <Route path="/settings/vault/index-builder" element={<SettingsVaultIndexBuilderPage />} />
          <Route path="/settings/config" element={<SettingsConfigPage />} />
          <Route path="/settings/ui" element={<SettingsUIPage />} />
          <Route path="/settings/artifacts" element={<SettingsArtifactsPage />} />
          <Route path="/settings/blueprints" element={<SettingsBlueprintsPage />} />
          <Route path="/settings/marketplace" element={<SettingsMarketplacePage />} />
          <Route path="/settings/export-data" element={<SettingsExportDataPage />} />
          <Route path="/settings/backup" element={<SettingsBackupPage />} />
          <Route path="/system-health" element={<SystemHealthPage />} />
          <Route path="/agent-activity" element={<AgentActivityPage />} />
          <Route path="/browse" element={<VaultBrowserPage />} />
          <Route path="/browse/:stem" element={<NoteDetailPage />} />
          <Route path="/vault" element={<VaultGraphPage />} />
          <Route path="/meeting-cockpit/:stem" element={<MeetingCockpitPage />} />
          <Route path="/inbox-cockpit/:stem" element={<InboxCockpitPage />} />
          {/* Installed plugins' screens (ADR-022), composed at build time. */}
          {pluginRoutes.map((route) => (
            <Route key={route.path} path={route.path} element={<route.component />} />
          ))}
          {pluginSettingsPages.map((page) => (
            <Route key={page.path} path={page.path} element={<page.component />} />
          ))}
        </Route>
        <Route path="/setup" element={<SetupPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
