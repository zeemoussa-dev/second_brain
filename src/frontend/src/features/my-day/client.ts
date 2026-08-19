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
