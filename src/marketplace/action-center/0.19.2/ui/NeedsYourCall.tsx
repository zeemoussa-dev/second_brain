import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link } from 'react-router';
import {
  fetchDoubts,
  setOwner,
  type Decision,
  type DoubtRow,
  type Doubts,
  type LookalikePair,
  type UnaddressedOwner,
} from './client';

/** What the agents could not settle, at the top of the screen -- with the
 *  control to settle it right there.
 *
 *  Counts alone were no use: they said something needed deciding and left
 *  nowhere to decide it (operator, 2026-09-24: "you are telling take action but
 *  I can't find what action I should Take"). Each row now states the one thing
 *  to do and does it on the spot, for the OWNER rather than per action -- one
 *  address settles every action that owner holds. What he decides is written to
 *  `Settings/Action-Owners.md` as his, and the agents read it before asking a
 *  model again. */
function OwnerRow({ owner, onDone }: { owner: UnaddressedOwner; onDone: () => void }) {
  const [address, setAddress] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  function save(email: string) {
    if (!email.trim()) return;
    setBusy(true);
    setError('');
    setOwner({ owner: owner.owner, email }).then(onDone, (e) => {
      setError(String(e instanceof Error ? e.message : e));
      setBusy(false);
    });
  }

  return (
    <li className="needs-call-owner">
      <div className="needs-call-owner-head">
        <strong>{owner.owner}</strong>
        <span className="text-muted">
          {owner.actions} action{owner.actions === 1 ? '' : 's'} · {owner.asks[0]}
        </span>
      </div>
      <form
        className="needs-call-owner-form"
        onSubmit={(event: FormEvent) => { event.preventDefault(); save(address); }}
      >
        {/* He sent the ask to whoever has to act, so the person in the To of
            his own mail comes first and says so -- "90% he will be in the to"
            (operator, 2026-09-26). A team keeps its name; naming somebody here
            says who acts for it. */}
        {owner.candidates.map((person) => (
          <button key={person.email}
                  type="button"
                  className={person.written_to ? 'btn btn-primary' : 'btn'}
                  disabled={busy}
                  title={person.written_to
                    ? `He wrote to ${person.email} on this thread — give ${owner.owner} that address`
                    : `Give ${owner.owner} this address (${person.email})`}
                  onClick={() => save(person.email)}>
            {person.name}{person.written_to ? ' ✓' : ''}
          </button>
        ))}
        <input className="input" type="email" placeholder="or type an address"
               value={address} onChange={(event) => setAddress(event.target.value)} />
        <button className="btn btn-primary" type="submit" disabled={busy || !address.trim()}>
          Save
        </button>
      </form>
      {error && <p className="text-warning">{error}</p>}
      <p className="needs-call-owner-links">
        {owner.stems.map((stem) => (
          <Link key={stem} to={`/action-center/action/${encodeURIComponent(stem)}`}>open</Link>
        ))}
      </p>
    </li>
  );
}

function PairRow({ pair, onDone }: { pair: LookalikePair; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [left, right] = pair;

  function keep(kept: typeof left, dropped: typeof left) {
    setBusy(true);
    setOwner({ owner: dropped.owner, name: kept.owner, email: kept.address ?? '' })
      .then(onDone, () => setBusy(false));
  }

  return (
    <li className="needs-call-pair">
      <span>
        <strong>{left.owner}</strong> <span className="text-muted">({left.actions})</span>
        <span className="text-muted"> or </span>
        <strong>{right.owner}</strong> <span className="text-muted">({right.actions})</span>
      </span>
      <span className="needs-call-pair-actions">
        <button type="button" className="btn" disabled={busy} onClick={() => keep(left, right)}>
          One person: {left.owner}
        </button>
        <button type="button" className="btn" disabled={busy} onClick={() => keep(right, left)}>
          One person: {right.owner}
        </button>
      </span>
    </li>
  );
}

function DecisionRow({ decision, onDone }: { decision: Decision; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  return (
    <li>
      {decision.seen} → {decision.name}
      {decision.email && <> &lt;{decision.email}&gt;</>}
      <span className="text-muted"> — {decision.by}, {decision.decided}</span>
      {decision.by === 'agent' && (
        <button type="button" className="btn needs-call-undo" disabled={busy}
                title="Clear the address and decide it yourself"
                onClick={() => {
                  setBusy(true);
                  setOwner({ owner: decision.seen, clear_address: true })
                    .then(onDone, () => setBusy(false));
                }}>
          Wrong
        </button>
      )}
    </li>
  );
}

function Actions({ items }: { items: DoubtRow[] }) {
  return (
    <ul className="needs-call-list">
      {items.map((item) => (
        <li key={item.stem}>
          <Link to={`/action-center/action/${encodeURIComponent(item.stem)}`}>{item.subject}</Link>
          <span className="text-muted"> — asked of {item.owner}</span>
        </li>
      ))}
    </ul>
  );
}

export function NeedsYourCall({ onChanged }: { onChanged: () => void }) {
  const [doubts, setDoubts] = useState<Doubts | null>(null);

  const load = useCallback(() => {
    fetchDoubts().then(setDoubts);
  }, []);
  useEffect(load, [load]);

  const settled = () => { load(); onChanged(); };

  if (!doubts) return <p className="text-muted">Loading…</p>;
  const total = doubts.asked_of_several.count + doubts.no_address.owners
    + doubts.possible_duplicate_owners.count;
  if (!total && !doubts.decided.count) {
    return (
      <div className="card">
        <div className="empty-state">
          <div className="empty-state-icon">&#10003;</div>
          <p><strong>Nothing is waiting on you.</strong></p>
          <p className="text-muted">Every owner has a name and an address.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card needs-call">
      <div className="needs-call-head">
        <h2>What the agents could not settle</h2>
        <span className="text-muted">
          {doubts.decided.count} settled, {doubts.decided.by_the_operator} by you
        </span>
      </div>

      {doubts.no_address.owners > 0 && (
        <section>
          <h3>
            Give these owners an address — {doubts.no_address.count} action
            {doubts.no_address.count === 1 ? '' : 's'} nobody can be messaged about
          </h3>
          <p className="text-muted">
            The buttons are the people he wrote the ask to. A team mailbox is fine.
          </p>
          <ul className="needs-call-owners">
            {doubts.no_address.items.map((owner) => (
              <OwnerRow key={owner.owner} owner={owner} onDone={settled} />
            ))}
          </ul>
        </section>
      )}

      {doubts.possible_duplicate_owners.count > 0 && (
        <section>
          <h3>One person, or two? — {doubts.possible_duplicate_owners.count} to say</h3>
          <p className="text-muted">
            Choosing a name moves the other one&apos;s actions onto it. Leave it if they are
            different people; nothing is merged without you.
          </p>
          <ul className="needs-call-list">
            {doubts.possible_duplicate_owners.items.map((pair) => (
              <PairRow key={pair.map((side) => side.owner).join('|')} pair={pair} onDone={settled} />
            ))}
          </ul>
        </section>
      )}

      {doubts.asked_of_several.count > 0 && (
        <section>
          <h3>Still asked of several people — {doubts.asked_of_several.count}</h3>
          <p className="text-muted">
            The split agent takes these hourly; open one to split it yourself.
          </p>
          <Actions items={doubts.asked_of_several.items} />
        </section>
      )}

      {doubts.decided.items.length > 0 && (
        <section>
          <h3>Settled</h3>
          <p className="text-muted">
            What the agents read before asking again. Mark an agent&apos;s call
            <strong> Wrong</strong> to clear it and decide it yourself.
          </p>
          <ul className="needs-call-list">
            {doubts.decided.items.map((decision) => (
              <DecisionRow key={decision.seen} decision={decision} onDone={settled} />
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
