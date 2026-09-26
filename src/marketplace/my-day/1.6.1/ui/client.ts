import { apiFetch, apiUrl } from '../../pluginHost/api';

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

/** A file captured with this Thread, under the subject's own `Files/` folder.
 * `filename` is the real file beside the attachment's note, or null when the
 * note was written without one. */
export interface ThreadAttachment {
  title: string;
  filename: string | null;
  stem: string;
}

/** What the Emails tab reads about one thread: what it is about, the emails it
 * is made of, and what came attached. */
export interface ThreadDetail {
  stem: string;
  subject: string;
  summary: string | null;
  emails: ThreadEmail[];
  attachments: ThreadAttachment[];
}

export function fetchThreadDetail(subjectNoteStem: string): Promise<ThreadDetail> {
  return apiFetch<ThreadDetail>(`${BASE}/threads/${encodeURIComponent(subjectNoteStem)}`);
}

export type ThreadEmailBody = ThreadEmail & { body: string };

/** One email's captured text. Fetched when it is opened, not with the thread:
 * a long thread would otherwise carry every body it never shows. */
export function fetchThreadEmail(subjectNoteStem: string, messageStem: string): Promise<ThreadEmailBody> {
  return apiFetch<ThreadEmailBody>(
    `${BASE}/threads/${encodeURIComponent(subjectNoteStem)}/emails/${encodeURIComponent(messageStem)}`,
  );
}

/** The real attachment file, as a URL the browser opens or downloads for itself
 * -- the framework serves a file sitting beside an indexed note (host `apiUrl`,
 * contract v6). */
export function attachmentUrl(noteStem: string, filename: string): string {
  return apiUrl(
    `/vault-search/notes/${encodeURIComponent(noteStem)}/assets/${encodeURIComponent(filename)}`,
  );
}
