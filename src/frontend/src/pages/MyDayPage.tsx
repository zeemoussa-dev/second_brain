import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';
import { fetchMyDaySummary, triggerMyDayRefresh, type MyDaySummary } from '../features/my-day/client';
import { fetchPendingApprovals } from '../features/agents-map/pendingApprovalsApiClient';

const SECTIONS = [
  { key: 'emails', label: 'Emails', href: '/my-day/emails' },
  { key: 'calendar', label: 'Calendar', href: '/my-day/calendar' },
  { key: 'todo', label: 'To-Do', href: '/my-day/todo' },
] as const;

function todayIso(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

function shiftDay(iso: string, delta: number): string {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + delta);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function formatDay(iso: string): string {
  return new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

function formatWindowRange(start: string, end: string): string {
  const fmt = (iso: string) =>
    new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  return `${fmt(start)} – ${fmt(end)}`;
}

export function MyDayPage() {
  const [selectedDay, setSelectedDay] = useState<string>(todayIso());
  const [summary, setSummary] = useState<MyDaySummary | null>(null);
  const [approvalsCount, setApprovalsCount] = useState<number | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  function reloadSummary() {
    fetchMyDaySummary(selectedDay).then(setSummary);
  }

  useEffect(() => {
    reloadSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDay]);

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshMessage(null);
    try {
      const outcomes = await triggerMyDayRefresh();
      const failed = outcomes.filter((o) => !o.triggered);
      setRefreshMessage(
        failed.length === 0
          ? 'Refresh triggered — new emails/meetings will show up once the capture run finishes.'
          : `Triggered, but ${failed.map((o) => o.pipeline_id).join(', ')} failed to start.`,
      );
    } catch {
      setRefreshMessage('Could not trigger refresh.');
    } finally {
      setRefreshing(false);
      reloadSummary();
    }
  }

  useEffect(() => {
    fetchPendingApprovals({ status: 'pending' }).then((items) => setApprovalsCount(items.length));
  }, []);

  const atWindowStart = summary?.window ? selectedDay <= summary.window.start : false;
  const atWindowEnd = summary?.window ? selectedDay >= summary.window.end : false;
  const isToday = selectedDay === todayIso();

  const sectionHrefs = useMemo(
    () => Object.fromEntries(SECTIONS.map((s) => [s.key, `${s.href}?day=${selectedDay}`])),
    [selectedDay],
  );

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
        <div>
          <h1 style={{ marginBottom: 'var(--space-2)' }}>My Day</h1>
          <p className="text-muted">
            The day's most important actions, surfaced from your background
            agents. Open a section for the full list.
          </p>
        </div>
        <button type="button" className="btn" data-testid="my-day-refresh" disabled={refreshing} onClick={handleRefresh}>
          {refreshing ? 'Refreshing…' : 'Refresh emails & meetings'}
        </button>
      </div>
      {refreshMessage && (
        <p className="text-muted" data-role="my-day-refresh-message" style={{ marginTop: 0 }}>
          {refreshMessage}
        </p>
      )}
      <div className="my-day-navigator">
        <button
          type="button"
          className="btn"
          onClick={() => setSelectedDay((d) => shiftDay(d, -1))}
          disabled={atWindowStart}
          aria-label="Previous day"
        >
          ←
        </button>
        <div className="my-day-navigator-current">
          <span className="my-day-navigator-day">{formatDay(selectedDay)}</span>
          {!isToday && (
            <button type="button" className="btn-link" onClick={() => setSelectedDay(todayIso())}>
              Jump to today
            </button>
          )}
        </div>
        <button
          type="button"
          className="btn"
          onClick={() => setSelectedDay((d) => shiftDay(d, 1))}
          disabled={atWindowEnd}
          aria-label="Next day"
        >
          →
        </button>
        {summary?.window && (
          <span className="my-day-window-range text-muted">
            {formatWindowRange(summary.window.start, summary.window.end)}
          </span>
        )}
      </div>
      <div className="day-section-grid">
        {SECTIONS.map((section) => {
          const count = summary?.[section.key].count;
          return (
            <Link key={section.key} className="card day-section-card" to={sectionHrefs[section.key]}>
              <h2>{section.label}</h2>
              {count && count > 0 ? (
                <div className="day-section-count">{count}</div>
              ) : (
                <span className="text-muted">Nothing captured yet</span>
              )}
            </Link>
          );
        })}
        <Link className="card day-section-card" to="/my-day/approvals">
          <h2>Pending Approvals</h2>
          {approvalsCount !== null && approvalsCount > 0 ? (
            <div className="day-section-count">{approvalsCount}</div>
          ) : (
            <span className="text-muted">Nothing awaiting approval yet</span>
          )}
        </Link>
      </div>
    </>
  );
}
