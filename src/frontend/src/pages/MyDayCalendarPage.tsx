import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router';
import { fetchMyDayCalendar, type MyDayCalendarItem } from '../features/my-day/client';

export function MyDayCalendarPage() {
  const [items, setItems] = useState<MyDayCalendarItem[] | null>(null);
  const [searchParams] = useSearchParams();
  const day = searchParams.get('day') ?? undefined;

  useEffect(() => {
    setItems(null);
    fetchMyDayCalendar(day).then(setItems);
  }, [day]);

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
      <h1>Calendar</h1>
      <p className="text-muted">
        {day ? `Meetings on ${day}` : "Today's meetings"}, filed by Meeting
        Capture (REQ-SB-08).
      </p>
      <div className="card">
        {items && items.length > 0 ? (
          <div className="item-list">
            {items.map((item, index) => (
              <div className="item-row" key={index}>
                <div className="item-row-main">
                  <span className="item-row-title">{item.subject}</span>
                  <span className="item-row-meta">
                    {item.start} &middot; {item.customer ?? 'No customer'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          items && (
            <div className="empty-state">
              <div className="empty-state-icon">&#128197;</div>
              <p><strong>No meetings captured yet.</strong></p>
              <p className="text-muted">
                Meeting Capture (REQ-SB-08) syncs on the same hourly
                schedule as email — nothing filed yet.
              </p>
            </div>
          )
        )}
      </div>
    </>
  );
}
