import type { PluginUi } from '../../pluginHost/types';
import { HomePage } from './HomePage';
import { PortfolioPage } from './PortfolioPage';
import { ReportPage } from './ReportPage';
import { SettingsPage } from './SettingsPage';
import './insight.css';

const ui: PluginUi = {
  routes: [
    { path: '/core42-insight', component: HomePage },
    { path: '/core42-insight/report', component: ReportPage },
    { path: '/core42-insight/portfolio', component: PortfolioPage },
  ],
  nav: [{ to: '/core42-insight', label: 'Insight', icon: '◈' }],
  settingsPages: [{ path: '', label: 'Core42 Insight', component: SettingsPage }],
};

export default ui;
