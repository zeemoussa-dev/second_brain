import { BrowserRouter, Routes, Route, Navigate } from 'react-router';
import { AppShell } from './components/shell/AppShell';
import { SetupPage } from './pages/SetupPage';
import { AgentsMapPage } from './pages/AgentsMapPage';
import { HermesProfileDetailPage } from './pages/HermesProfileDetailPage';
import { ChatPage } from './pages/ChatPage';
import { CrawlersPage } from './pages/CrawlersPage';
import { CrawlerDetailPage } from './pages/CrawlerDetailPage';
import { SettingsPage } from './pages/SettingsPage';
import { SettingsActionsPage } from './pages/SettingsActionsPage';
import { SettingsArtifactsPage } from './pages/SettingsArtifactsPage';
import { SettingsWorkflowsPage } from './pages/SettingsWorkflowsPage';
import { SettingsBlueprintsPage } from './pages/SettingsBlueprintsPage';
import { SettingsMarketplacePage } from './pages/SettingsMarketplacePage';
import { SettingsOperatorPage } from './pages/SettingsOperatorPage';
import { SettingsSystemPage } from './pages/SettingsSystemPage';
import { SettingsUsersPage } from './pages/SettingsUsersPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsBrandingPage } from './pages/SettingsBrandingPage';
import { AdminCenterPage } from './pages/AdminCenterPage';
import { SessionTranscriptPage } from './pages/SessionTranscriptPage';
import { EntryPointsPage } from './pages/EntryPointsPage';
import { WaitingOnMePage } from './pages/WaitingOnMePage';
import { SettingsAgentAccessPage } from './pages/SettingsAgentAccessPage';
import { FlowMapPage } from './pages/FlowMapPage';
import { AgentFlowPage } from './pages/AgentFlowPage';
import { SettingsRulesPage } from './pages/SettingsRulesPage';
import { SettingsSectionsPage } from './pages/SettingsSectionsPage';
import { SettingsVaultPage } from './pages/SettingsVaultPage';
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
import { NoteDetailPage } from './pages/NoteDetailPage';
import { MeetingCockpitPage } from './pages/MeetingCockpitPage';
import { InboxCockpitPage } from './pages/InboxCockpitPage';
import { pluginRoutes, pluginSettingsPages } from './pluginHost/registry';
import { PluginSettingsTrail } from './pluginHost/breadcrumbs';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<AgentsMapPage />} />
          {/* The read-only Hermes profile debug view (ADR-043) -- its own URL
              so it can be pasted into an incident note, not an eighth panel tab. */}
          <Route path="/agents/:agentId/profile" element={<HermesProfileDetailPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/crawlers" element={<CrawlersPage />} />
          {/* One crawler, on its own page (REQ-SB-102). */}
          <Route path="/crawlers/:jobId" element={<CrawlerDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          {/* Running the install, split out of Settings on 2026-10-21. */}
          <Route path="/admin" element={<AdminCenterPage />} />
          <Route path="/settings/system" element={<SettingsSystemPage />} />
          <Route path="/settings/operator" element={<SettingsOperatorPage />} />
          <Route path="/settings/users" element={<SettingsUsersPage />} />
          <Route path="/settings/branding" element={<SettingsBrandingPage />} />
          {/* The keys Hermes workers authenticate with (REQ-SB-103). */}
          <Route path="/settings/agent-access" element={<SettingsAgentAccessPage />} />
          {/* Your own account (REQ-SB-101). Not under /settings: it is
              not a setting of the install, it is one person's account,
              and everyone signed in has one regardless of role. */}
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/settings/sections" element={<SettingsSectionsPage />} />
          <Route path="/settings/vault" element={<SettingsVaultPage />} />
          <Route path="/settings/vault/templates" element={<SettingsVaultTemplatesPage />} />
          <Route path="/settings/vault/index-filtering" element={<SettingsVaultIndexFilteringPage />} />
          <Route path="/settings/vault/index-builder" element={<SettingsVaultIndexBuilderPage />} />
          <Route path="/settings/config" element={<SettingsConfigPage />} />
          <Route path="/settings/ui" element={<SettingsUIPage />} />
          <Route path="/settings/artifacts" element={<SettingsArtifactsPage />} />
          <Route path="/settings/actions" element={<SettingsActionsPage />} />
          <Route path="/settings/workflows" element={<SettingsWorkflowsPage />} />
          <Route path="/settings/blueprints" element={<SettingsBlueprintsPage />} />
          <Route path="/settings/marketplace" element={<SettingsMarketplacePage />} />
          <Route path="/settings/export-data" element={<SettingsExportDataPage />} />
          <Route path="/settings/backup" element={<SettingsBackupPage />} />
          <Route path="/system-health" element={<SystemHealthPage />} />
          <Route path="/agent-activity" element={<AgentActivityPage />} />
          {/* REQ-SB-100 / REQ-SB-102 -- one session read as a
              conversation, and the outside doors into this install. */}
          <Route path="/agent-activity/:sessionId" element={<SessionTranscriptPage />} />
          <Route path="/entry-points" element={<EntryPointsPage />} />
          {/* Workflows that stopped to ask a person (REQ-SB-103). */}
          <Route path="/waiting-on-me" element={<WaitingOnMePage />} />
          <Route path="/flow" element={<FlowMapPage />} />
          {/* One agent's own slice of the flow (REQ-SB-102). */}
          <Route path="/flow/:agentId" element={<AgentFlowPage />} />
          <Route path="/settings/rules" element={<SettingsRulesPage />} />
          <Route path="/browse" element={<VaultBrowserPage />} />
          <Route path="/browse/:stem" element={<NoteDetailPage />} />
          {/* The graph is a VIEW of the vault now, not a screen of its own
              (operator, 2026-10-24: "Need to Merge the Vault with the
              Search"). The old URL keeps working and lands on that view, so
              a link pasted into a note still opens what it promised. */}
          <Route path="/vault" element={<Navigate to="/browse?view=graph" replace />} />
          <Route path="/meeting-cockpit/:stem" element={<MeetingCockpitPage />} />
          <Route path="/inbox-cockpit/:stem" element={<InboxCockpitPage />} />
          {/* Installed plugins' screens (ADR-022), composed at build time. */}
          {pluginRoutes.map((route) => (
            <Route key={route.path} path={route.path} element={<route.component />} />
          ))}
          {/* A plugin's Settings page lives under the host's /settings, an area
              the plugin does not own, so the host renders its trail (API 11). */}
          {pluginSettingsPages.map((page) => (
            <Route
              key={page.path}
              path={page.path}
              element={<><PluginSettingsTrail page={page} /><page.component /></>}
            />
          ))}
        </Route>
        <Route path="/setup" element={<SetupPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
