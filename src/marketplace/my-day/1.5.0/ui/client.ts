import { apiFetch } from '../../pluginHost/api';

// The host mounts this plugin's backend under /plugins/<plugin-id>/.
const BASE = '/plugins/my-day';

function withDay(path: string, day?: string): string {
  return day ? `${BASE}${path}?day=${day}` : `${BASE}${path}`;
}

export interface MyDaySummary {
  emails: { count: number };
  calendar: { count: number };
  todo: { count: number };
  window: { start: string; end: string };
}

export function fetchMyDaySummary(day?: string): Promise<MyDaySummary> {
  return apiFetch<MyDaySummary>(withDay('/summary', day));
}

export interface MyDayEmailItem {
  subject: string;
  sender: string;
  customer: string | null;
  received: string;
  stem: string;
}

export function fetchMyDayEmails(day?: string): Promise<MyDayEmailItem[]> {
  return apiFetch<MyDayEmailItem[]>(withDay('/emails', day));
}

export interface MyDayCalendarItem {
  subject: string;
  start: string;
  customer: string | null;
  stem: string;
}

export function fetchMyDayCalendar(day?: string): Promise<MyDayCalendarItem[]> {
  return apiFetch<MyDayCalendarItem[]>(withDay('/calendar', day));
}

export interface MyDayTodoItem {
  subject: string;
  customer: string | null;
  due: string | null;
}

export function fetchMyDayTodo(): Promise<MyDayTodoItem[]> {
  return apiFetch<MyDayTodoItem[]>(`${BASE}/todo`);
}

export interface MyDayRefreshOutcome {
  pipeline_id: string;
  triggered: boolean;
  detail: string;
}

// Resolves once the triggers are sent, not once capture finishes
// (operator, 2026-09-02: "the Option to pull stuff manually").
export function triggerMyDayRefresh(): Promise<MyDayRefreshOutcome[]> {
  return apiFetch<MyDayRefreshOutcome[]>(`${BASE}/refresh`, { method: 'POST' });
}

/** One real email inside a captured Thread -- its own note under the Thread's
 * `messages/` folder. */
export interface ThreadEmail {
  stem: string;
  subject: string;
  sender: string;
  sender_email: string;
  received: string;
}

export function fetchThreadEmails(subjectNoteStem: string): Promise<ThreadEmail[]> {
  return apiFetch<ThreadEmail[]>(`${BASE}/threads/${encodeURIComponent(subjectNoteStem)}/emails`);
}
