import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import {
  fetchPendingApprovals,
  approvePendingApproval,
  declinePendingApproval,
  type PendingApproval,
} from '../features/agents-map/pendingApprovalsApiClient';

export function MyDayApprovalsPage() {
  const [items, setItems] = useState<PendingApproval[] | null>(null);

  function refresh() {
    fetchPendingApprovals({ status: 'pending' }).then(setItems);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleApprove(id: string) {
    await approvePendingApproval(id);
    refresh();
  }

  async function handleDecline(id: string) {
    await declinePendingApproval(id);
    refresh();
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
      <h1>Pending Approvals</h1>
      <p className="text-muted">
        Actions a Supervised agent has proposed on its own background/
        scheduled pipeline trigger and is waiting on your approval before
        taking. Chat-triggered proposals from an active conversation
        appear inline in that agent's own Chat panel on the Agents Map
        instead of here. Change an agent's working mode from its Agent
        Settings panel.
      </p>
      <div className="card">
        {items && items.length > 0 ? (
          <div className="item-list">
            {items.map((item) => (
              <div className="item-row" key={item.id}>
                <div className="item-row-main">
                  <span className="item-row-title">
                    {item.agent_name} <span className="badge badge-warning">Awaiting approval</span>
                  </span>
                  <span className="item-row-meta">{item.description}</span>
                </div>
                <div className="item-row-actions">
                  <button type="button" className="btn btn-primary" onClick={() => handleApprove(item.id)}>
                    Approve
                  </button>
                  <button type="button" className="btn btn-danger" onClick={() => handleDecline(item.id)}>
                    Decline
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          items && (
            <div className="empty-state">
              <div className="empty-state-icon">&#10003;</div>
              <p><strong>Nothing awaiting approval right now.</strong></p>
              <p className="text-muted">
                Every Supervised agent's queue is caught up. Proposals from
                a background/scheduled pipeline trigger will appear here
                as soon as one is raised.
              </p>
            </div>
          )
        )}
      </div>
    </>
  );
}
