import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { fetchMyDayEmails, type MyDayEmailItem } from '../features/my-day/client';

export function MyDayEmailsPage() {
  const [items, setItems] = useState<MyDayEmailItem[] | null>(null);
  const [searchParams] = useSearchParams();
  const day = searchParams.get('day') ?? undefined;

  useEffect(() => {
    setItems(null);
    fetchMyDayEmails(day).then(setItems);
  }, [day]);

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
      <h1>Emails</h1>
      <p className="text-muted">
        {day ? `Email captured on ${day}` : 'Recently captured email'}, filed
        by Email Capture (REQ-SB-07).
      </p>
      <div className="card">
        {items && items.length > 0 ? (
          <div className="item-list">
            {items.map((item, index) => (
              <div className="item-row" key={index}>
                <div className="item-row-main">
                  <span className="item-row-title">{item.subject}</span>
                  <span className="item-row-meta">
                    {item.received} &middot; {item.customer ?? 'Unclassified'} &middot; from {item.sender}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          items && (
            <div className="empty-state">
              <div className="empty-state-icon">&#9993;</div>
              <p><strong>No emails captured yet.</strong></p>
              <p className="text-muted">
                Email Capture runs hourly and once on app start — check
                back after the next run.
              </p>
            </div>
          )
        )}
      </div>
    </>
  );
}
