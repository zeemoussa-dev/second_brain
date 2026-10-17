import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router';
import { ApiError } from '../../pluginHost/api';
import { createAction, type NewAction } from './client';

/** An action added by hand. It is the same Task note the mail pass and the
 *  agents write, marked `source: manual`, so every list and filter holds it. */
export function NewActionPanel() {
  const navigate = useNavigate();
  const [fields, setFields] = useState<NewAction>({ subject: '', scope: 'waiting', priority: 'Normal' });
  const [error, setError] = useState('');
  const set = (key: keyof NewAction) => (e: { target: { value: string } }) =>
    setFields((current) => ({ ...current, [key]: e.target.value }));

  function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    createAction(fields).then(
      ({ stem }) => navigate(`/action-center/action/${encodeURIComponent(stem)}`),
      (e) => setError(e instanceof ApiError ? e.message : String(e)),
    );
  }

  return (
    <>
      <p className="text-muted">
        Added by hand. It becomes the same Task note the mail pass and the agents
        write, so every list, filter and agent holds it.
      </p>
      <div className="card">
        <form className="action-form action-form-grid" onSubmit={submit}>
          <label className="action-form-wide">The ask
            <input className="input" required value={fields.subject} onChange={set('subject')} />
          </label>
          <label>Owner<input className="input" value={fields.owner ?? ''} onChange={set('owner')} /></label>
          <label>Owner's email<input className="input" value={fields.owner_email ?? ''} onChange={set('owner_email')} /></label>
          <label>Due<input className="input" type="date" value={fields.due ?? ''} onChange={set('due')} /></label>
          <label>Priority
            <select className="input" value={fields.priority} onChange={set('priority')}>
              {['Low', 'Normal', 'High'].map((p) => <option key={p}>{p}</option>)}
            </select>
          </label>
          <label>Whose
            <select className="input" value={fields.scope} onChange={set('scope')}>
              <option value="waiting">Waiting on others</option>
              <option value="mine">Mine</option>
            </select>
          </label>
          <label>Customer<input className="input" value={fields.customer ?? ''} onChange={set('customer')} /></label>
          <label className="action-form-wide">Context
            <textarea className="input" rows={3} value={fields.note ?? ''} onChange={set('note')} />
          </label>
          {error && <p className="text-warning action-form-wide">{error}</p>}
          <div className="action-form-wide">
            <button className="btn btn-primary" type="submit" disabled={!fields.subject.trim()}>Add action</button>
          </div>
        </form>
      </div>
    </>
  );
}
