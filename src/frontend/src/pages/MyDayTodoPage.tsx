import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { fetchMyDayTodo, type MyDayTodoItem } from '../features/my-day/client';

function todayIso(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

function dueBadge(due: string | null): { label: string; warning: boolean } | null {
  if (!due) return null;
  const dueDate = due.slice(0, 10);
  if (dueDate === todayIso()) {
    return { label: 'Due today', warning: true };
  }
  return { label: 'Upcoming', warning: false };
}

export function MyDayTodoPage() {
  const [items, setItems] = useState<MyDayTodoItem[] | null>(null);

  useEffect(() => {
    fetchMyDayTodo().then(setItems);
  }, []);

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
      <h1>To-Do</h1>
      <p className="text-muted">Tasks captured by To-Do Capture (REQ-SB-09).</p>
      <div className="card">
        {items && items.length > 0 ? (
          <div className="item-list">
            {items.map((item, index) => {
              const badge = dueBadge(item.due);
              return (
                <div className="item-row" key={index}>
                  <div className="item-row-main">
                    <span className="item-row-title">{item.subject}</span>
                    <span className="item-row-meta">
                      {item.customer ?? 'No customer'} &middot; {item.due ? item.due.slice(0, 10) : 'No due date'}
                    </span>
                  </div>
                  {badge && (
                    <span className={badge.warning ? 'badge badge-warning' : 'badge'}>
                      {badge.label}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          items && (
            <div className="empty-state">
              <div className="empty-state-icon">&#9745;</div>
              <p><strong>No tasks captured yet.</strong></p>
              <p className="text-muted">
                To-Do Capture runs hourly and once on app start — check
                back after the next run.
              </p>
            </div>
          )
        )}
      </div>
    </>
  );
}
