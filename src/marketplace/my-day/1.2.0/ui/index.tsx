import type { PluginUi } from '../../pluginHost/types';
import { DayPage } from './DayPage';
import { EmailsPage } from './EmailsPage';
import { CalendarPage } from './CalendarPage';
import { TodoPage } from './TodoPage';
import './my-day.css';

const ui: PluginUi = {
  routes: [
    { path: '/my-day', component: DayPage },
    { path: '/my-day/emails', component: EmailsPage },
    { path: '/my-day/calendar', component: CalendarPage },
    { path: '/my-day/todo', component: TodoPage },
  ],
  nav: [{ to: '/my-day', label: 'My Day', icon: '☀' }],
};

export default ui;
