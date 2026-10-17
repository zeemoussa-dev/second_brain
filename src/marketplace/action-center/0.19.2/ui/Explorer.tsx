import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';
import { useUrlState, useUrlFilters } from '../../pluginHost/state';
import {
  chaseMany,
  fetchActionFacets,
  fetchActionGroups,
  type ActionCenterSummary,
  type ActionFacets,
  type ActionFilters,
  type ActionGroup,
  type ActionItem,
} from './client';

/** The list itself: search, filters, grouping, and the groups.
 *
 *  Written once and used by both the open screen and the completed one
 *  (operator, 2026-09-25: "I need to have the same filters and Grouping for
 *  the completed tasks"). What was done is a record worth interrogating the
 *  same way as what is outstanding -- what did this customer ever ask of us,
 *  what has this person actually delivered -- and a flat list of the last
 *  hundred cannot answer that.
 *
 *  The two differ only where the work differs: an open action is read by who
 *  owes it and how late it is, a completed one by when it closed and what
 *  showed it.
 */
const GROUP_LABELS: Record<string, string> = {
  owner: 'Owner',
  addressable: 'Can be messaged',
  customer: 'Customer',
  status: 'Status',
  source: 'Source',
  scope: 'Mine / waiting',
  due: 'Due',
  completed: 'When it closed',
  owner_kind: 'A person or a team',
  entity: 'Company',
};

// What he is waiting on and what he owes are different work; a single list
// mixing them reads as one long backlog.
const SCOPE_TABS = [
  { value: 'waiting', label: 'Waiting on others' },
  { value: 'mine', label: 'Mine' },
  { value: '', label: 'All' },
];

const SOURCE_LABELS: Record<string, string> = {
  email: 'from sent mail',
  agent: 'asked an agent',
  manual: 'added by hand',
};

function ActionRow({ item, closed }: { item: ActionItem; closed: boolean }) {
  const meta = closed
    ? [
      item.owner || 'Unassigned',
      item.customer,
      item.completed_at ? `completed ${item.completed_at.slice(0, 10)}` : 'no date recorded',
      // The evidence is the point of the completed list: "done" with nothing
      // behind it is a guess, and this is where a wrong judgment shows.
      item.evidence || 'no evidence recorded',
    ].filter(Boolean)
    : [
      item.owner_email || 'no address',
      item.customer,
      item.due ? `due ${item.due}` : 'no due date',
      item.asked_at ? `asked ${item.asked_at.slice(0, 10)}` : null,
      SOURCE_LABELS[item.source] ?? item.source,
    ].filter(Boolean);

  return (
    <Link className="item-row action-row-link" to={`/action-center/action/${encodeURIComponent(item.stem)}`}>
      <div className="item-row-main">
        <span className="item-row-title">{item.subject}</span>
        <span className="item-row-meta">{meta.join(' · ')}</span>
      </div>
      {/* "Core42 Commercial" is an honest answer to who was asked and a
          misleading one to who will act: say which it is on the row. */}
      {!closed && item.owner_is_person === false
        && <span className="badge" title="A team or company — nobody named yet">Not a person</span>}
      {!closed && item.owner_is_person !== false && !item.owner_email
        && <span className="badge" title="Nobody to message about this yet">No address</span>}
      {!closed && item.keep_open_until
        && <span className="badge" title={`Open until ${item.keep_open_until}`}>Held</span>}
      {!closed && item.overdue && <span className="badge badge-warning">Overdue</span>}
      {closed && !item.evidence && <span className="badge badge-warning">No evidence</span>}
      {closed && item.evidence && !item.evidence_source
        && <span className="badge" title="The quote is here; what it came from is not">No source</span>}
    </Link>
  );
}

/** Chase everything in a list at once -- one group, or everything shown.
 *
 *  It is still one email per action, written separately by the agent (operator,
 *  2026-09-24: "Still it will go one by one but Just for a faster execution").
 *  What is saved is the pressing, not the writing, so the confirmation says how
 *  many emails are about to be written and to how many people. Nothing
 *  completed is chaseable, so this disappears on that screen by itself.
 */
function ChaseAll({ items, what, onDone }: {
  items: ActionItem[]; what: string; onDone: () => void;
}) {
  const [state, setState] = useState<'idle' | 'asking' | 'asked'>('idle');
  const [said, setSaid] = useState('');

  const chaseable = items.filter(
    (item) => item.status === 'Open' && item.scope !== 'mine' && item.owner_email);
  if (chaseable.length === 0) return null;
  const people = new Set(chaseable.map((item) => item.owner_email)).size;

  function chase() {
    if (!window.confirm(
      `Send ${chaseable.length} email${chaseable.length === 1 ? '' : 's'} now`
      + ` to ${people} ${people === 1 ? 'person' : 'people'} — ${what}?\n\n`
      + `One email per action, each written by the agent and sent from`
      + ` cbo-agent01@core42.ai. They cannot be unsent.`)) {
      return;
    }
    setState('asking');
    chaseMany(chaseable.map((item) => item.stem)).then((answer) => {
      setState('asked');
      setSaid(`${answer.queued} queued. ${answer.note}`);
      onDone();
    }, () => setState('idle'));
  }

  return (
    <span className="action-center-chase-all">
      <button type="button" className="btn" disabled={state !== 'idle'} onClick={chase}>
        {state === 'asking' ? 'Asking the agent…'
          : state === 'asked' ? 'Queued' : `Chase all ${chaseable.length}`}
      </button>
      {said && <span className="text-muted"> {said}</span>}
    </span>
  );
}

// Every filter the board offers, with the value each falls back to. A field at
// its default is dropped from the URL, so an untouched board has a clean
// address. `scope: 'waiting'` is the open board's own default view -- what is
// owed by other people -- and `undefined` means "no filter".
const FILTER_DEFAULTS_OPEN = {
  scope: 'waiting' as string, owner: undefined as string | undefined,
  customer: undefined as string | undefined, source: undefined as string | undefined,
  priority: undefined as string | undefined, entity: undefined as string | undefined,
  entity_tag: undefined as string | undefined, q: undefined as string | undefined,
  overdue: false, unaddressed: false, not_a_person: false, no_source: false,
};
const FILTER_DEFAULTS_CLOSED = { ...FILTER_DEFAULTS_OPEN, scope: undefined as unknown as string };

export function ActionExplorer({ status, summary, onChanged }: {
  status: 'Open' | 'Completed';
  summary: ActionCenterSummary | null;
  onChanged: () => void;
}) {
  const closed = status === 'Completed';
  const [facets, setFacets] = useState<ActionFacets | null>(null);
  // Grouping and every filter live in the query string, so a refresh keeps the
  // board where it was and the address can be sent to whoever is being chased
  // (framework ADR-041). `status` is the tab the screen was opened as and stays
  // a prop.
  const [groupBy, setGroupBy] = useUrlState<string>('group', closed ? 'completed' : 'owner');
  const [urlFilters, setFilterField] = useUrlFilters(
    closed ? FILTER_DEFAULTS_CLOSED : FILTER_DEFAULTS_OPEN);
  // Memoised: this object is a dependency of the fetch effect below, so a
  // fresh identity every render would loop it forever.
  const filters: ActionFilters = useMemo(() => ({ ...urlFilters, status }), [urlFilters, status]);
  const [groups, setGroups] = useState<ActionGroup[] | null>(null);

  useEffect(() => { fetchActionFacets(status).then(setFacets); }, [status]);

  useEffect(() => {
    setGroups(null);
    fetchActionGroups(groupBy, filters).then(setGroups);
  }, [groupBy, filters]);

  const shown = useMemo(() => (groups ?? []).flatMap((group) => group.items), [groups]);
  const total = shown.length;
  const withEvidence = useMemo(() => shown.filter((item) => item.evidence).length, [shown]);
  // Evidence that links to nothing is a weaker kind of closed: the quote is
  // there, the thing it came from is not, so nobody can go and look.
  const unsourced = useMemo(
    () => shown.filter((item) => item.evidence && !item.evidence_source).length, [shown]);
  const people = useMemo(
    () => new Set(shown.map((item) => item.owner).filter(Boolean)).size, [shown]);

  function set(field: keyof ActionFilters, value: string | boolean) {
    setFilterField(field as keyof typeof urlFilters & string, value);
  }

  return (
    <>
      <div className="action-center-tabs">
        {SCOPE_TABS.map((tab) => (
          <button
            key={tab.value || 'all'}
            type="button"
            className={(filters.scope ?? '') === tab.value ? 'is-selected' : undefined}
            onClick={() => set('scope', tab.value)}
          >
            {tab.label}
            {!closed && summary && tab.value === 'waiting' ? ` (${summary.waiting_on_others})` : ''}
            {!closed && summary && tab.value === 'mine' ? ` (${summary.mine})` : ''}
          </button>
        ))}
      </div>

      {closed ? (
        <div className="action-center-stats">
          <span><strong>{total}</strong> shown</span>
          <span><strong>{people}</strong> people</span>
          <span><strong>{withEvidence}</strong> with evidence</span>
          <span className={unsourced ? 'text-warning' : undefined}>
            <strong>{unsourced}</strong> with no source
          </span>
          <span className={total - withEvidence ? 'text-warning' : undefined}>
            <strong>{total - withEvidence}</strong> closed on nothing
          </span>
        </div>
      ) : summary && (
        <div className="action-center-stats">
          <span><strong>{summary.open}</strong> open</span>
          <span className={summary.overdue ? 'text-warning' : undefined}>
            <strong>{summary.overdue}</strong> overdue
          </span>
          <span><strong>{summary.owners}</strong> people</span>
          <span><strong>{summary.completed}</strong> completed</span>
          <span className={summary.unaddressed ? 'text-warning' : undefined}>
            <strong>{summary.unaddressed}</strong> with no address
          </span>
          {summary.not_a_person !== undefined && (
            <span className={summary.not_a_person ? 'text-warning' : undefined}>
              <strong>{summary.not_a_person}</strong> owed by a team
            </span>
          )}
        </div>
      )}

      <div className="action-center-filters">
        <input
          type="search"
          placeholder="Search the ask, owner or customer"
          value={filters.q ?? ''}
          onChange={(event) => set('q', event.target.value)}
        />
        {/* On the completed screen the status IS the screen; offering to filter
            it away would empty the list it is on. */}
        {!closed && (
          <select value={filters.status ?? ''} onChange={(event) => set('status', event.target.value)}>
            <option value="">Any status</option>
            {facets?.statuses.map((facet) => (
              <option key={facet.value} value={facet.value}>{facet.value} ({facet.count})</option>
            ))}
          </select>
        )}
        <select value={filters.owner ?? ''} onChange={(event) => set('owner', event.target.value)}>
          <option value="">Anyone</option>
          {facets?.owners.map((facet) => (
            <option key={facet.value} value={facet.value}>{facet.value} ({facet.count})</option>
          ))}
        </select>
        {/* What the action is about, taken from its thread's own company tag
            -- the CBO reads this board by account at least as often as by
            person (operator, 2026-09-29). */}
        <select value={filters.entity ?? ''} onChange={(event) => set('entity', event.target.value)}>
          <option value="">Any company</option>
          {(facets?.entities ?? []).map((facet) => (
            <option key={facet.value} value={facet.value}>{facet.value} ({facet.count})</option>
          ))}
        </select>
        <select value={filters.customer ?? ''} onChange={(event) => set('customer', event.target.value)}>
          <option value="">Any customer</option>
          {facets?.customers.map((facet) => (
            <option key={facet.value} value={facet.value}>{facet.value} ({facet.count})</option>
          ))}
        </select>
        <select value={filters.source ?? ''} onChange={(event) => set('source', event.target.value)}>
          <option value="">Any source</option>
          {facets?.sources.map((facet) => (
            <option key={facet.value} value={facet.value}>
              {SOURCE_LABELS[facet.value] ?? facet.value} ({facet.count})
            </option>
          ))}
        </select>
        {!closed && (
          <label className="action-center-toggle">
            <input
              type="checkbox"
              checked={Boolean(filters.overdue)}
              onChange={(event) => set('overdue', event.target.checked)}
            />
            Overdue only
          </label>
        )}
        <label className="action-center-toggle">
          <input
            type="checkbox"
            checked={Boolean(filters.unaddressed)}
            onChange={(event) => set('unaddressed', event.target.checked)}
          />
          No address
        </label>
        {/* A count nobody can act on is what this screen was told off for
            once; the number is also a filter. */}
        {!closed && (
          <label className="action-center-toggle"
                 title="Owned by a team or a company, with nobody named to do it">
            <input
              type="checkbox"
              checked={Boolean(filters.not_a_person)}
              onChange={(event) => set('not_a_person', event.target.checked)}
            />
            Not a person
          </label>
        )}
        {closed && (
          <label className="action-center-toggle"
                 title="Closed on something nobody can go and check: no link back, or no evidence at all">
            <input
              type="checkbox"
              checked={Boolean(filters.no_source)}
              onChange={(event) => set('no_source', event.target.checked)}
            />
            No source only
          </label>
        )}
        <span className="action-center-groupby">
          Group by
          <select value={groupBy} onChange={(event) => setGroupBy(event.target.value)}>
            {(facets?.group_by ?? [groupBy]).map((value) => (
              <option key={value} value={value}>{GROUP_LABELS[value] ?? value}</option>
            ))}
          </select>
        </span>
      </div>

      {groups && (
        <p className="text-muted action-center-count">
          {total} action{total === 1 ? '' : 's'} in {groups.length} group
          {groups.length === 1 ? '' : 's'}
          <ChaseAll items={shown} what="everything shown" onDone={onChanged} />
        </p>
      )}

      {groups && groups.length > 0 ? (
        groups.map((group) => (
          <div className="card action-center-group" key={group.key}>
            <div className="action-center-group-head">
              <h2>{group.key}</h2>
              <span className="text-muted">
                {group.count} {closed ? 'completed' : 'open'}
                {!closed && group.overdue > 0 ? ` · ${group.overdue} overdue` : ''}
                <ChaseAll items={group.items} what={group.key} onDone={onChanged} />
              </span>
            </div>
            <div className="item-list">
              {group.items.map((item) => (
                <ActionRow key={item.stem} item={item} closed={closed} />
              ))}
            </div>
          </div>
        ))
      ) : (
        groups && (
          <div className="card">
            <div className="empty-state">
              <div className="empty-state-icon">{closed ? '✓' : '☐'}</div>
              <p><strong>{closed ? 'Nothing completed matches.' : 'No actions match.'}</strong></p>
              <p className="text-muted">
                {closed
                  ? 'Clear the filters. An action appears here once it is closed, with whatever showed that it happened.'
                  : 'Clear the filters, or wait for the next pass over sent mail. An agent can also be asked to add one directly.'}
              </p>
            </div>
          </div>
        )
      )}
    </>
  );
}
