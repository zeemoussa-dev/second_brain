import { useEffect, useMemo, useState, type MouseEvent, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router';
import { ApiError } from '../../pluginHost/api';
import { useRememberedState, useUrlFilters } from '../../pluginHost/state';
import { fetchCustomerList, fetchCustomerRow, fetchSettings, type CustomerDetail, type CustomerStatus, type ListedCustomer } from './client';
import { errorText, formatMonth, reportLink, usd } from './format';

// The same screen as Azure Cost's customer portfolio (operator, 2026-10-18), with
// Insight's own columns. Copied, not imported: a plugin imports no other plugin.
// It loads lazily (operator, 2026-10-18: "Use Lazy Loading to fill the data"): the
// fast list draws every row at once, then each row's figures arrive on their own.

/** Rows asked for at once: enough to fill the screen quickly, few enough not to starve the backend. */
const ROW_REQUESTS_AT_ONCE = 4;
/** A 503 means the vault is still loading after a backend reload: wait, then ask again. */
const VAULT_RETRY_MS = 5000;
const VAULT_RETRIES = 6;

type Row = ListedCustomer & Partial<CustomerDetail> & { loaded: boolean; failed?: string };

const STATUS_LABELS: Record<CustomerStatus, string> = {
  active: 'Insight active',
  inherited: 'Follows parent',
  ended: 'Terms ended',
  'no-terms': 'No Insight',
  unreadable: 'Terms do not read',
};
// What needs attention first.
const STATUS_ORDER: CustomerStatus[] = ['unreadable', 'active', 'inherited', 'ended', 'no-terms'];

const FILTERS = ['all', 'active', 'inherited', 'no-terms', 'no-agreement', 'groups', 'standalone'] as const;
type Filter = typeof FILTERS[number];
const FILTER_LABELS: Record<Filter, string> = {
  all: 'All', active: 'Insight active', inherited: 'Follows parent', 'no-terms': 'No Insight', 'no-agreement': 'No agreement',
  groups: 'Groups', standalone: 'Standalone',
};

const SORTS = ['name', 'agreement', 'last', 'trend', 'ytd', 'forecast', 'status'] as const;
type Sort = typeof SORTS[number];

function matchesFilter(row: Row, show: Filter): boolean {
  if (!['all', 'groups', 'standalone'].includes(show) && !row.loaded) return false;
  if (show === 'active') return row.status === 'active';
  if (show === 'inherited') return row.status === 'inherited';
  if (show === 'no-terms') return row.status === 'no-terms';
  if (show === 'no-agreement') return !row.agreement && !row.agreement_from;
  return true;
}

function sortValue(row: Row, sort: Sort): number | string {
  const recent = row.recent ?? [];
  switch (sort) {
    case 'name': return row.name.toLowerCase();
    case 'agreement': return row.agreement?.amount ?? -1;
    case 'last': return recent.length ? recent[recent.length - 1].revenue : -1;
    case 'trend': return row.mom_pct ?? -Infinity;
    case 'ytd': return row.summary?.ytd ?? -1;
    case 'forecast': return row.summary?.forecast_year_end ?? -1;
    // A row still loading sorts after every known status.
    case 'status': return row.status ? STATUS_ORDER.indexOf(row.status) : STATUS_ORDER.length;
  }
}

function compare(sort: Sort, descending: boolean) {
  return (a: Row, b: Row) => {
    const left = sortValue(a, sort);
    const right = sortValue(b, sort);
    const order = left < right ? -1 : left > right ? 1 : a.name.localeCompare(b.name);
    return descending ? -order : order;
  };
}

function Sparkline({ points }: { points: { revenue: number }[] }) {
  if (points.length < 2) return null;
  const values = points.map((point) => point.revenue);
  const low = Math.min(...values);
  const span = Math.max(...values) - low || 1;
  const path = values.map((value, index) =>
    `${(index / (values.length - 1)) * 80},${20 - ((value - low) / span) * 18 - 1}`).join(' ');
  return (
    <svg className="insight-sparkline" viewBox="0 0 80 20" width="80" height="20" aria-hidden="true">
      <polyline points={path} fill="none" strokeWidth="1.5" />
    </svg>
  );
}

const day = (value: string | null | undefined) => (value ? value.slice(0, 10) : '?');

/** Every customer at a glance, each group's affiliates folded under it; a row opens its Insight report. */
export function CustomerChooser() {
  const navigate = useNavigate();
  const [listed, setListed] = useState<ListedCustomer[] | null>(null);
  const [details, setDetails] = useState<Record<string, CustomerDetail>>({});
  const [failures, setFailures] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  // Without Entities no customer's terms can be read: say so once, rather than
  // drawing every customer as "No Insight" (2026-10-18).
  const [entitiesDown, setEntitiesDown] = useState(false);
  const [filters, setFilter] = useUrlFilters({ search: '', show: 'all', sort: 'status' });
  const [expanded, setExpanded] = useRememberedState<string[]>('core42-insight.expanded-groups', []);

  useEffect(() => {
    fetchSettings().then((settings) => {
      setEntitiesDown(!settings.sources.entities);
      if (settings.sources.entities) fetchCustomerList().then(setListed, (failure) => setError(errorText(failure)));
    }, (failure) => setError(errorText(failure)));
  }, []);

  // Each row's figures on its own request, a few at a time, top-level customers
  // first -- they are what the folded screen shows.
  useEffect(() => {
    if (!listed) return undefined;
    let stopped = false;
    const queue = [...listed.filter((row) => !row.parent), ...listed.filter((row) => row.parent)].map((row) => row.stem);
    const tries: Record<string, number> = {};
    const fetchRow = async (key: string): Promise<void> => {
      try {
        const detail = await fetchCustomerRow(key);
        if (!stopped) setDetails((current) => ({ ...current, [key]: detail }));
      } catch (failure) {
        tries[key] = (tries[key] ?? 0) + 1;
        // Never shown as "no Insight": a vault still loading is a wait, not an answer.
        if (failure instanceof ApiError && failure.status === 503 && tries[key] < VAULT_RETRIES) {
          await new Promise((resolve) => setTimeout(resolve, VAULT_RETRY_MS));
          if (!stopped) await fetchRow(key);
          return;
        }
        if (!stopped) setFailures((current) => ({ ...current, [key]: errorText(failure) }));
      }
    };
    const work = async () => {
      for (let stem = queue.shift(); stem !== undefined && !stopped; stem = queue.shift()) {
        await fetchRow(stem);
      }
    };
    for (let worker = 0; worker < ROW_REQUESTS_AT_ONCE; worker += 1) void work();
    return () => { stopped = true; };
  }, [listed]);

  const rows = useMemo<Row[] | null>(() => listed && listed.map((row) => ({
    ...row, ...details[row.stem], loaded: Boolean(details[row.stem]), failed: failures[row.stem],
  })), [listed, details, failures]);
  const pending = rows ? rows.filter((row) => !row.loaded && !row.failed).length : 0;

  const show = (FILTERS as readonly string[]).includes(filters.show) ? filters.show as Filter : 'all';
  const descending = filters.sort.startsWith('-');
  const sortKey = filters.sort.replace(/^-/, '');
  const sort = (SORTS as readonly string[]).includes(sortKey) ? sortKey as Sort : 'status';
  const needle = filters.search.trim().toLowerCase();
  const narrowing = Boolean(needle) || !['all', 'groups', 'standalone'].includes(show);

  const visible = useMemo(() => {
    if (!rows) return [];
    const byStem = new Map(rows.map((row) => [row.stem, row]));
    const matches = (row: Row) => (!needle || row.name.toLowerCase().includes(needle)) && matchesFilter(row, show);
    const tops = rows.filter((row) => !row.parent || !byStem.has(row.parent))
      .filter((row) => show !== 'groups' || row.affiliates.length > 0)
      .filter((row) => show !== 'standalone' || row.affiliates.length === 0);
    const ordering = compare(sort, descending);
    return tops.map((top) => {
      const affiliates = top.affiliates.map((stem) => byStem.get(stem)).filter((row): row is Row => Boolean(row));
      const hits = narrowing ? affiliates.filter(matches) : affiliates;
      return { top, affiliates: hits.sort(ordering), total: affiliates.length, shown: matches(top) || hits.length > 0 };
    }).filter((group) => group.shown).sort((a, b) => ordering(a.top, b.top));
  }, [rows, needle, show, sort, descending, narrowing]);

  if (entitiesDown) {
    return (
      <div className="insight-error">
        The Entities plugin is not running, so Insight cannot read customers' terms. They are safe in the vault and
        show again as soon as Entities runs. Check Settings &gt; Plugins: Entities may need updating for this
        framework version.
      </div>
    );
  }
  if (error) return <div className="insight-error">{error}</div>;
  if (!rows) return <p className="text-muted">Loading customers…</p>;
  if (rows.length === 0) return <p className="empty-state">No Azure Cost Manager customer is linked to a Customer note yet.</p>;

  const groups = rows.filter((row) => row.affiliates.length > 0).map((row) => row.stem);
  const isOpen = (stem: string) => narrowing || expanded.includes(stem);
  const toggle = (event: MouseEvent, stem: string) => {
    event.stopPropagation();
    setExpanded(expanded.includes(stem) ? expanded.filter((open) => open !== stem) : [...expanded, stem]);
  };
  const counts: Partial<Record<Filter, number>> = {
    active: rows.filter((row) => row.status === 'active').length,
    inherited: rows.filter((row) => row.status === 'inherited').length,
    'no-terms': rows.filter((row) => row.status === 'no-terms').length,
    'no-agreement': rows.filter((row) => row.loaded && !row.agreement && !row.agreement_from).length,
  };

  const header = (key: Sort, label: string) => (
    <th aria-sort={sort === key ? (descending ? 'descending' : 'ascending') : undefined}>
      <button type="button" className="insight-sort" onClick={() => {
        const startDescending = key !== 'name' && key !== 'status';
        const nextDescending = sort === key ? !descending : startDescending;
        setFilter('sort', nextDescending ? `-${key}` : key);
      }}>{label}{sort === key ? (descending ? ' ↓' : ' ↑') : ''}</button>
    </th>
  );

  const line = (row: Row, affiliate: boolean, total = 0) => {
    const recent = row.recent ?? [];
    const last = recent.length ? recent[recent.length - 1] : null;
    // A figure cell before its row has arrived: a placeholder, or why it could not load.
    const cell = (content: () => ReactNode) => (row.loaded ? content()
      : row.failed ? <span className="insight-warn" title={row.failed}>not loaded</span>
        : <span className="insight-loading" aria-label="Loading" />);
    return (
      <tr key={row.stem} className={affiliate ? 'insight-chooser-affiliate' : 'insight-chooser-top'}
          onClick={() => navigate(reportLink(row.stem))}>
        <td>
          {!affiliate && total > 0 ? (
            <button type="button" className="insight-twisty" aria-expanded={isOpen(row.stem)} disabled={narrowing}
                    aria-label={`${isOpen(row.stem) ? 'Collapse' : 'Expand'} ${row.name}'s affiliates`}
                    onClick={(event) => toggle(event, row.stem)}>{isOpen(row.stem) ? '▾' : '▸'}</button>
          ) : <span className="insight-twisty-space" />}
          <Link to={reportLink(row.stem)} onClick={(event) => event.stopPropagation()}>{row.name}</Link>
          <div className="text-muted insight-row-detail">
            {total > 0 ? `${total} affiliate${total === 1 ? '' : 's'}` : affiliate ? 'affiliate' : 'standalone'}
            {row.has_note ? '' : ' · no Customer note'}
          </div>
        </td>
        <td>{cell(() => (row.agreement ? (
          <>
            {row.agreement.type || 'Agreement'}{row.agreement.amount ? ` ${usd(row.agreement.amount, true)}` : ''}
            <div className="text-muted insight-row-detail">{day(row.agreement.start)} → {day(row.agreement.end)}</div>
          </>
        ) : row.agreement_from ? (
          <span className="text-muted" title="It signs no agreement of its own; its consumption counts toward its parent's">
            In {row.agreement_from}'s agreement</span>
        ) : '—'))}</td>
        <td>{cell(() => (
          <>
            {row.in_force ?? <span className="text-muted">—</span>}
            {row.inherited_from && row.in_force ? <div className="text-muted insight-row-detail">from {row.inherited_from}</div> : null}
          </>
        ))}</td>
        <td>{cell(() => (last ? <>{usd(last.revenue, true)}
          <div className="text-muted insight-row-detail">{formatMonth(last.month, true)}</div></> : '—'))}</td>
        <td>{cell(() => (
          <div className="insight-trend">
            <Sparkline points={recent} />
            {row.mom_pct != null ? (
              <span className={row.mom_pct >= 0 ? 'insight-up' : 'insight-down'}>
                {row.mom_pct >= 0 ? '+' : ''}{row.mom_pct}%</span>
            ) : null}
          </div>
        ))}</td>
        <td>{cell(() => (row.summary ? usd(row.summary.ytd, true) : '—'))}</td>
        <td>{cell(() => (row.summary ? usd(row.summary.forecast_year_end, true) : '—'))}</td>
        <td>{cell(() => (row.status ? (
          <span className={`insight-status ${row.status}`} title={row.terms_error ?? undefined}>{STATUS_LABELS[row.status]}</span>
        ) : null))}</td>
      </tr>
    );
  };

  return (
    <section className="card insight-card">
      <div className="insight-card-head">
        <div className="insight-chips" role="group" aria-label="Show">
          {FILTERS.map((filter) => (
            <button key={filter} type="button" className={show === filter ? 'active' : undefined}
                    aria-pressed={show === filter} onClick={() => setFilter('show', filter)}>
              {FILTER_LABELS[filter]}
              {counts[filter] ? <span className="insight-chip-count">{counts[filter]}</span> : null}
            </button>
          ))}
        </div>
        <div className="insight-toolbar">
          {pending ? <span className="text-muted" aria-live="polite">Loading figures… {rows.length - pending} of {rows.length}</span> : null}
          {groups.length ? (
            <>
              <button type="button" className="btn" disabled={narrowing} onClick={() => setExpanded(groups)}>Expand all</button>
              <button type="button" className="btn" disabled={narrowing} onClick={() => setExpanded([])}>Collapse all</button>
            </>
          ) : null}
          <input type="search" placeholder="Search customers and affiliates" value={filters.search}
                 onChange={(event) => setFilter('search', event.target.value)} aria-label="Search customers" />
        </div>
      </div>
      <table className="insight-chooser">
        <thead>
          <tr>
            {header('name', 'Customer')}
            {header('agreement', 'Agreement')}
            <th>Insight terms</th>
            {header('last', 'Last month')}
            {header('trend', 'Trend')}
            {header('ytd', 'Year to date')}
            {header('forecast', 'Forecast to year end')}
            {header('status', 'Status')}
          </tr>
        </thead>
        <tbody>
          {visible.flatMap(({ top, affiliates, total }) => [
            line(top, false, total),
            ...(isOpen(top.stem) ? affiliates.map((affiliate) => line(affiliate, true)) : []),
          ])}
        </tbody>
      </table>
      {visible.length === 0 ? <p className="text-muted">No customer matches.</p> : null}
    </section>
  );
}
