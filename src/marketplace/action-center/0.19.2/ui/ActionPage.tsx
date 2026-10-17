import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router';
import { ApiError } from '../../pluginHost/api';
import {
  addActionNote,
  chaseOwner,
  completeAction,
  fetchAction,
  fetchChaseRecipients,
  reopenAction,
  updateAction,
  type ActionDetail,
  type ChaseRecipient,
  type LinkedNote,
} from './client';

const SCOPE_LABELS: Record<string, string> = { waiting: 'Waiting on others', mine: 'Mine' };
const SOURCE_LABELS: Record<string, string> = {
  email: 'read out of sent mail',
  agent: 'recorded by an agent',
  manual: 'added by hand',
};

/** The host answers a refused write with `{"detail": "..."}`; show the reason. */
function reason(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      return JSON.parse(error.message).detail ?? error.message;
    } catch {
      return error.message;
    }
  }
  return String(error);
}

/** A thread or meeting this action points at. The Cockpit is where the
 *  conversation continues -- ask an agent about it, draft the follow-up -- so
 *  it is the first way in; the plain note is always there too. */
function LinkedRow({ label, link, empty }: { label: string; link: LinkedNote | null; empty: string }) {
  return (
    <div className="action-link-row">
      <span className="action-link-label">{label}</span>
      {link ? (
        <span className="action-link-target">
          <span className="action-link-name">{link.stem}</span>
          {link.kind && <span className="badge">{link.kind}</span>}
          {link.cockpit && <Link className="btn btn-primary" to={link.cockpit}>Open in Cockpit</Link>}
          {link.found ? <Link className="btn" to={link.note}>View note</Link>
            : <span className="text-muted">not in the vault index</span>}
        </span>
      ) : (
        <span className="text-muted">{empty}</span>
      )}
    </div>
  );
}

/** Chasing is on the operator's press, never on a schedule (operator,
 *  2026-09-24). The agent writes the message for THIS ask -- one action, one
 *  email -- and IT SENDS -- he asked for that once he had read what it writes.
 *  So the press is confirmed first: it reaches a colleague, and there is no
 *  taking it back. */
function ChaseButton({ action, onDone }: { action: ActionDetail; onDone: () => void }) {
  const [state, setState] = useState<'idle' | 'asking' | 'asked'>('idle');
  const [said, setSaid] = useState('');
  // Who it would go to, and who he left ticked. An ask owed by two people is
  // one email to both (operator, 2026-09-26), so the list is shown before
  // sending -- everyone ticked -- and he can take off whoever has already done
  // their half rather than nudging them for it again.
  const [people, setPeople] = useState<ChaseRecipient[] | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  // Whether this action already carries a list he settled on: it is written to
  // the note, so it survives the press and an unattended chase would read it.
  const [settled, setSettled] = useState(false);
  // How many OTHER actions this one email covers: the split pass writes an
  // action per person, and "each team VP to book a call" is one ask.
  const [shared, setShared] = useState(0);

  const open = action.status === 'Open' && action.scope !== 'mine';
  useEffect(() => {
    if (!open) return;
    fetchChaseRecipients(action.stem).then((answer) => {
      setPeople(answer.recipients);
      setPicked(answer.recipients.filter((p) => p.selected).map((p) => p.email));
      setSettled(answer.settled.length > 0);
      setShared(answer.shared_with);
    }, () => setPeople([]));
  }, [action.stem, open]);

  if (!open) return null;
  if (people === null) return <span className="text-muted">Checking who owes this…</span>;

  const addressable = people.filter((person) => person.email && !person.external);
  if (!addressable.length) {
    return (
      <span className="text-muted">
        {people.some((person) => person.external)
          ? 'Everyone who owes this is outside the company, and chases are set to colleagues only.'
          : 'No address to chase — settle the owner first.'}
      </span>
    );
  }

  function chase() {
    const going = addressable.filter((person) => picked.includes(person.email));
    if (!going.length) return;
    const listed = going.map((person) => `${person.name || person.email} <${person.email}>`).join('\n  ');
    if (!window.confirm(
      `Send one email now about this action, to:\n  ${listed}\n\n`
      + 'The agent writes it and sends it from cbo-agent01@core42.ai. It cannot be unsent.')) {
      return;
    }
    setState('asking');
    chaseOwner(action.stem, going.map((person) => person.email)).then((answer) => {
      setState('asked');
      setSaid(answer.note);
      onDone();
    }, (error) => {
      setState('idle');
      setSaid(reason(error));
    });
  }

  return (
    <>
      <button type="button" className="btn" disabled={state !== 'idle' || !picked.length}
              onClick={chase}
              title={`One email to ${picked.length} of the ${addressable.length} this is owed by`}>
        {state === 'asking' ? 'Asking the agent…' : state === 'asked' ? 'Chase sent'
          : `Chase ${picked.length > 1 ? `${picked.length} people ` : ''}(sends email)`}
      </button>
      <div className="action-chase-people">
        <span className="text-muted">
          {shared > 0
            ? `The same ask is open on ${shared + 1} people — one email to all of them,`
              + ' and each still closes on its own:'
            : addressable.length > 1
              ? 'One email, everyone in To — untick anyone who should not get it:'
              : 'Goes to:'}
          {settled && ' kept from last time, and what a later chase will use.'}
        </span>
        {people.map((person) => (
          <label key={person.email || person.name}
                 className={'action-chase-person'
                   + (person.email ? '' : ' is-unknown')
                   + (person.external ? ' is-external' : '')}
                 title={person.external
                   ? 'outside the company — chases are set to colleagues only'
                   : person.email ? `known from the ${person.source}` : 'no address for this name'}>
            <input type="checkbox"
                   disabled={!person.email || person.external || state !== 'idle'}
                   checked={picked.includes(person.email)}
                   onChange={(event) => setPicked((chosen) => (event.target.checked
                     ? [...chosen, person.email]
                     : chosen.filter((email) => email !== person.email)))} />
            {person.name || person.email}
            {person.email
              ? <span className="text-muted"> &lt;{person.email}&gt;</span>
              : <span className="text-muted"> — no address</span>}
            {person.external && <span className="text-muted"> — outside the company</span>}
          </label>
        ))}
      </div>
      {said && <span className="text-muted action-chase-said">{said}</span>}
    </>
  );
}

function CloseForm({ action, onDone }: { action: ActionDetail; onDone: () => void }) {
  const [evidence, setEvidence] = useState('');
  const [source, setSource] = useState(action.source_link?.stem ?? '');
  const [dropped, setDropped] = useState(false);
  const [conditionMet, setConditionMet] = useState(false);
  const [error, setError] = useState('');
  const held = Boolean(action.keep_open_until) && !dropped;

  function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    completeAction(action.stem, {
      evidence, status: dropped ? 'Dropped' : 'Completed',
      evidence_source: source, condition_met: conditionMet,
    }).then(onDone, (e) => setError(reason(e)));
  }

  return (
    <form className="action-form" onSubmit={submit}>
      <h3>Close it</h3>
      <label>
        What shows it is done
        <textarea className="input" rows={2} required value={evidence}
                  onChange={(e) => setEvidence(e.target.value)}
                  placeholder="Quote the reply, or name the meeting and its date" />
      </label>
      <label>
        Where that came from (thread or meeting)
        <input className="input" value={source} onChange={(e) => setSource(e.target.value)} />
      </label>
      <label className="action-check">
        <input type="checkbox" checked={dropped} onChange={(e) => setDropped(e.target.checked)} />
        Drop it instead -- it stopped mattering rather than being done
      </label>
      {held && (
        <label className="action-check">
          <input type="checkbox" checked={conditionMet} onChange={(e) => setConditionMet(e.target.checked)} />
          This shows that {action.keep_open_until}
        </label>
      )}
      {error && <p className="text-warning">{error}</p>}
      <button className="btn btn-primary" type="submit" disabled={!evidence.trim() || (held && !conditionMet)}>
        {dropped ? 'Drop' : 'Mark done'}
      </button>
    </form>
  );
}

function ReopenForm({ action, onDone }: { action: ActionDetail; onDone: () => void }) {
  const [why, setWhy] = useState('');
  const [until, setUntil] = useState(action.keep_open_until ?? '');
  const [error, setError] = useState('');

  function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    reopenAction(action.stem, { reason: why, keep_open_until: until }).then(onDone, (e) => setError(reason(e)));
  }

  return (
    <form className="action-form" onSubmit={submit}>
      <h3>Reopen it</h3>
      <label>
        Why it is not done
        <input className="input" required value={why} onChange={(e) => setWhy(e.target.value)} />
      </label>
      <label>
        Keep it open until (optional)
        <input className="input" value={until} onChange={(e) => setUntil(e.target.value)}
               placeholder="e.g. the invoices are paid" />
      </label>
      {error && <p className="text-warning">{error}</p>}
      <button className="btn btn-primary" type="submit" disabled={!why.trim()}>Reopen</button>
    </form>
  );
}

function EditForm({ action, onDone }: { action: ActionDetail; onDone: () => void }) {
  const [fields, setFields] = useState({
    subject: action.subject, owner: action.owner, owner_email: action.owner_email,
    due: action.due ?? '', priority: action.priority, scope: action.scope,
    customer: action.customer ?? '', keep_open_until: action.keep_open_until ?? '',
  });
  const [error, setError] = useState('');
  const set = (key: keyof typeof fields) => (e: { target: { value: string } }) =>
    setFields((current) => ({ ...current, [key]: e.target.value }));

  function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    updateAction(action.stem, fields).then(onDone, (e) => setError(reason(e)));
  }

  return (
    <form className="action-form action-form-grid" onSubmit={submit}>
      <label className="action-form-wide">The ask<input className="input" value={fields.subject} onChange={set('subject')} /></label>
      <label>Owner<input className="input" value={fields.owner} onChange={set('owner')} /></label>
      <label>Owner's email<input className="input" value={fields.owner_email} onChange={set('owner_email')} /></label>
      <label>Due<input className="input" type="date" value={fields.due} onChange={set('due')} /></label>
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
      <label>Customer<input className="input" value={fields.customer} onChange={set('customer')} /></label>
      <label className="action-form-wide">Keep open until
        <input className="input" value={fields.keep_open_until} onChange={set('keep_open_until')} />
      </label>
      {error && <p className="text-warning action-form-wide">{error}</p>}
      <div className="action-form-wide"><button className="btn btn-primary" type="submit">Save</button></div>
    </form>
  );
}

function NoteForm({ stem, onDone }: { stem: string; onDone: () => void }) {
  const [text, setText] = useState('');
  const [error, setError] = useState('');

  function submit(event: FormEvent) {
    event.preventDefault();
    addActionNote(stem, text).then(() => { setText(''); onDone(); }, (e) => setError(reason(e)));
  }

  return (
    <form className="action-note-form" onSubmit={submit}>
      <input className="input" value={text} onChange={(e) => setText(e.target.value)}
             placeholder="Add a note -- the completion agent reads these" />
      <button className="btn" type="submit" disabled={!text.trim()}>Add note</button>
      {error && <p className="text-warning">{error}</p>}
    </form>
  );
}

/** One action, opened: where it came from, what closed it, its history, the
 *  operator's notes -- and the controls to close, reopen, edit and annotate it. */
export function ActionPage() {
  const { stem = '' } = useParams<{ stem: string }>();
  const [action, setAction] = useState<ActionDetail | null>(null);
  const [missing, setMissing] = useState(false);
  const [editing, setEditing] = useState(false);

  const load = useCallback(() => {
    fetchAction(stem).then(setAction, (e) => {
      if (e instanceof ApiError && e.status === 404) setMissing(true);
      else throw e;
    });
  }, [stem]);

  useEffect(load, [load]);

  const back = <p className="text-muted"><Link className="text-muted" to="/action-center">&larr; Action Center</Link></p>;
  if (missing) return <>{back}<div className="card"><p>No action named "{stem}".</p></div></>;
  if (!action) return <>{back}<p className="text-muted">Loading...</p></>;

  const isOpen = action.status === 'Open';
  const facts: [string, string | null][] = [
    ['Owner', action.owner || 'Unassigned'],
    ['Whose', SCOPE_LABELS[action.scope] ?? action.scope],
    ['Due', action.due ?? 'no due date'],
    ['Asked', action.asked_at?.slice(0, 10) ?? null],
    ['Customer', action.customer],
    ['Priority', action.priority],
    ['Source', SOURCE_LABELS[action.source] ?? action.source],
    ['Closed', action.completed_at?.slice(0, 10) ?? null],
  ];

  return (
    <>
      {back}
      <div className="card action-detail-head">
        <div className="action-detail-badges">
          <span className="badge">{action.status}</span>
          {action.overdue && <span className="badge badge-warning">Overdue</span>}
        </div>
        <h1>{action.subject}</h1>
        {action.keep_open_until && (
          <p className="action-hold">Stays open until {action.keep_open_until}.</p>
        )}
        <dl className="action-facts">
          {facts.filter(([, value]) => value).map(([label, value]) => (
            <div key={label}><dt>{label}</dt><dd>{value}</dd></div>
          ))}
        </dl>
        <div className="action-detail-controls">
          <button type="button" className="btn" onClick={() => setEditing((v) => !v)}>
            {editing ? 'Cancel edit' : 'Edit'}
          </button>
          <Link className="btn" to={`/browse/${encodeURIComponent(action.stem)}`}>Open the Task note</Link>
          <ChaseButton action={action} onDone={load} />
        </div>
        {editing && <EditForm action={action} onDone={() => { setEditing(false); load(); }} />}
      </div>

      <div className="card">
        <h2>Links</h2>
        <LinkedRow label="Came from" link={action.source_link} empty="no thread recorded -- added by hand or by an agent" />
        <LinkedRow label="Closed by" link={action.evidence_link}
                   empty={isOpen ? 'not closed yet' : 'no source recorded for the evidence'} />
        {action.evidence && <blockquote className="action-evidence">{action.evidence}</blockquote>}
      </div>

      {action.ask && (
        <div className="card"><h2>The ask</h2><p className="action-ask">{action.ask}</p></div>
      )}

      <div className="card">
        <h2>History</h2>
        {action.history.length ? (
          <ul className="action-lines">{action.history.map((line, i) => <li key={i}>{line}</li>)}</ul>
        ) : <p className="text-muted">Nothing recorded yet.</p>}
      </div>

      {action.chases.length > 0 && (
        <div className="card">
          <h2>Chased</h2>
          <ul className="action-lines">{action.chases.map((line, i) => <li key={i}>{line}</li>)}</ul>
        </div>
      )}

      <div className="card">
        <h2>Notes</h2>
        {action.notes.length > 0 && (
          <ul className="action-lines">{action.notes.map((line, i) => <li key={i}>{line}</li>)}</ul>
        )}
        <NoteForm stem={action.stem} onDone={load} />
      </div>

      <div className="card">
        {isOpen ? <CloseForm action={action} onDone={load} /> : <ReopenForm action={action} onDone={load} />}
      </div>
    </>
  );
}
