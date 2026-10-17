import type { PluginUi } from '../../pluginHost/types';
import { ActionCenterPage } from './ActionCenterPage';
import { ActionPage } from './ActionPage';
import './action-center.css';

/** One screen, four tabs, four URLs. The tabs are routes rather than local
 *  state so a tab can be linked to, opened in a new window and gone back from
 *  (operator, 2026-09-24: tabs for Completed, New action, Current, and the
 *  things needing his input, "instead of appearing at the top"). */
const ui: PluginUi = {
  routes: [
    { path: '/action-center', component: ActionCenterPage },
    { path: '/action-center/needs-you', component: ActionCenterPage },
    { path: '/action-center/completed', component: ActionCenterPage },
    { path: '/action-center/new', component: ActionCenterPage },
    { path: '/action-center/action/:stem', component: ActionPage },
  ],
  nav: [{ to: '/action-center', label: 'Action Center', icon: '\u2611' }],
};

export default ui;
