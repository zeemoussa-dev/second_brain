import { apiFetch } from '../../api/client';

export interface MyDaySummary {
  emails: { count: number };
  calendar: { count: number };
  todo: { count: number };
  window: { start: string; end: string };
}

export function fetchMyDaySummary(day?: string): Promise<MyDaySummary> {
  return apiFetch<MyDaySummary>(day ? `/my-day/summary?day=${day}` : '/my-day/summary');
}

export interface MyDayEmailItem {
  subject: string;
  sender: string;
  customer: string | null;
  received: string;
  stem: string;
}

export function fetchMyDayEmails(day?: string): Promise<MyDayEmailItem[]> {
  return apiFetch<MyDayEmailItem[]>(day ? `/my-day/emails?day=${day}` : '/my-day/emails');
}

export interface MyDayCalendarItem {
  subject: string;
  start: string;
  customer: string | null;
  stem: string;
}

export function fetchMyDayCalendar(day?: string): Promise<MyDayCalendarItem[]> {
  return apiFetch<MyDayCalendarItem[]>(day ? `/my-day/calendar?day=${day}` : '/my-day/calendar');
}

export interface MyDayTodoItem {
  subject: string;
  customer: string | null;
  due: string | null;
}

export function fetchMyDayTodo(): Promise<MyDayTodoItem[]> {
  return apiFetch<MyDayTodoItem[]>('/my-day/todo');
}

export interface MyDayRefreshOutcome {
  pipeline_id: string;
  triggered: boolean;
  detail: string;
}

// Manually fires the real capture pipelines behind Emails/Calendar
// (operator, 2026-09-02: "the Option to pull stuff manually") --
// fire-and-forget, resolves once the trigger request is sent, not once
// the real capture run finishes.
export function triggerMyDayRefresh(): Promise<MyDayRefreshOutcome[]> {
  return apiFetch<MyDayRefreshOutcome[]>('/my-day/refresh', { method: 'POST' });
}
