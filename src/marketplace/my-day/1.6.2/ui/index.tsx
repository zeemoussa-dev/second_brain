import type { PluginUi } from '../../pluginHost/types';
import { DayPage } from './DayPage';
import { EmailsPage } from './EmailsPage';
import { CalendarPage } from './CalendarPage';
import { TodoPage } from './TodoPage';
import { ThreadEmailsTab } from './ThreadEmailsTab';
import './my-day.css';

const ui: PluginUi = {
  routes: [
    { path: '/my-day', component: DayPage },
    { path: '/my-day/emails', component: EmailsPage },
    { path: '/my-day/calendar', component: CalendarPage },
    { path: '/my-day/todo', component: TodoPage },
  ],
  nav: [{ to: '/my-day', label: 'My Day', icon: '☀' }],
  // The Cockpit is the framework's generic component for chatting with agents
  // about a subject; a Thread's own emails is knowledge about email, which is
  // this plugin's (operator, 2026-09-24: "Cockpit is the framework Peice as
  // Component for Agents to chat its Used inside myDay which understands Emails
  // and Calendar"). Host contract v3.
  cockpitTabs: [{
    subjectKind: 'email', id: 'emails', label: 'Emails', icon: '✉', component: ThreadEmailsTab,
  }],
};

export default ui;
