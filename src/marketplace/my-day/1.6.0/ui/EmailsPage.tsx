import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { fetchMyDayEmails, type MyDayEmailItem } from './client';
import { ThreadReader } from './ThreadReader';

// A list beside a reader, rather than a list that links away: the thread's
// summary, its emails and its attachments are on the same screen as the list
// (operator, 2026-09-25: "We need to make the email more useful"). The selected
// thread lives in the URL, so a particular email is a link someone can keep.

export function EmailsPage() {
  const [items, setItems] = useState<MyDayEmailItem[] | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const day = searchParams.get('day') ?? undefined;
  const selected = searchParams.get('thread');

  useEffect(() => {
    let cancelled = false;
    setItems(null);
    fetchMyDayEmails(day).then((result) => !cancelled && setItems(result));
    return () => {
      cancelled = true;
    };
  }, [day]);

  function select(stem: string) {
    const next = new URLSearchParams(searchParams);
    next.set('thread', stem);
    // Replaced, not pushed: clicking through a list should not fill the back
    // button with every thread that was glanced at.
    setSearchParams(next, { replace: true });
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
      <h1>Emails</h1>
      <p className="text-muted">
        {day ? `Email captured on ${day}` : 'Recently captured email'}, filed
        by Email Capture. Pick a thread to read it.
      </p>
      {items && items.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">&#9993;</div>
            <p><strong>No emails captured yet.</strong></p>
            <p className="text-muted">
              Email Capture runs hourly and once on app start — check
              back after the next run.
            </p>
          </div>
        </div>
      ) : (
        <div className="my-day-emails-split">
          <div className="card my-day-email-index">
            {items ? (
              <div className="item-list">
                {items.map((item) => (
                  <button
                    type="button"
                    className={`item-row my-day-email-index-row${item.stem === selected ? ' is-selected' : ''}`}
                    onClick={() => select(item.stem)}
                    aria-current={item.stem === selected}
                    key={item.stem}
                  >
                    <span className="item-row-main">
                      <span className="item-row-title">{item.subject}</span>
                      <span className="item-row-meta">
                        {item.received} &middot; {item.customer ?? 'Unclassified'} &middot; from {item.sender}
                      </span>
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-muted" role="status">Loading the emails…</p>
            )}
          </div>
          {selected ? (
            <ThreadReader stem={selected} key={selected} />
          ) : (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">&#9993;</div>
                <p className="text-muted">Pick a thread on the left to read it here.</p>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
