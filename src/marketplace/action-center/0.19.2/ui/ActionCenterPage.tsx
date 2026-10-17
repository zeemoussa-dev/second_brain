import { useCallback, useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router';
import { CompletedPanel } from './CompletedPage';
import { ActionExplorer } from './Explorer';
import { NeedsYourCall } from './NeedsYourCall';
import { NewActionPanel } from './NewActionPage';
import {
  fetchActionSummary,
  fetchChaseRules,
  saveChaseRules,
  type ActionCenterSummary,
} from './client';

/** The four faces of the Action Center, as URLs rather than local state: a tab
 *  can be linked to, opened in its own window and gone back from (operator,
 *  2026-09-24). "Needs your input" is one of them now -- it used to sit on top
 *  of the list, which made every visit start with a to-do list of its own.
 *
 *  Current and Completed are the same screen over different work: the list,
 *  its filters and its grouping live in `Explorer.tsx` and are built once
 *  (operator, 2026-09-25). */
const TABS = [
  { path: '/action-center', label: 'Current' },
  { path: '/action-center/needs-you', label: 'Needs your input' },
  { path: '/action-center/completed', label: 'Completed' },
  { path: '/action-center/new', label: 'New action' },
];

/** The standing rule for chasing, where he can see it and turn it off.
 *
 *  Pressing Chase is a decision about one email; a job that fires on a schedule
 *  is a standing permission, and this is the bound on it he asked for while
 *  that is still being built (operator, 2026-09-26: "for now only send to
 *  internal people ... we can uncheck this later"). It is not a screen
 *  preference: the Skill the cron job runs reads the same setting and refuses
 *  an outside address whoever asks. */
function ChaseRules() {
  const [internalOnly, setInternalOnly] = useState<boolean | null>(null);
  const [domains, setDomains] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetchChaseRules().then((rule) => {
      setInternalOnly(rule.internal_only);
      setDomains(rule.domains);
    }, () => setInternalOnly(null));
  }, []);

  if (internalOnly === null) return null;

  function change(wanted: boolean) {
    if (!wanted && !window.confirm(
      'Let the agent chase people outside the company?\n\n'
      + 'Chases are written and sent by the agent, and a scheduled one goes out with'
      + ' nobody watching. Until now it could only write to colleagues.')) {
      return;
    }
    setBusy(true);
    saveChaseRules(wanted).then((rule) => {
      setInternalOnly(rule.internal_only);
      setBusy(false);
    }, () => setBusy(false));
  }

  return (
    <label className="action-center-rule" title="Read by the screen and by the job that chases">
      <input type="checkbox" checked={internalOnly} disabled={busy}
             onChange={(event) => change(!event.target.checked)} />
      Chase only people inside the company
      {domains.length ? <span className="text-muted"> ({domains.join(', ')})</span> : null}
    </label>
  );
}

export function ActionCenterPage() {
  const here = useLocation().pathname.replace(/\/$/, '') || '/action-center';
  const [summary, setSummary] = useState<ActionCenterSummary | null>(null);

  const reload = useCallback(() => { fetchActionSummary().then(setSummary); }, []);
  useEffect(reload, [reload]);

  const counts: Record<string, number | undefined> = {
    '/action-center': summary?.open,
    '/action-center/needs-you': summary?.unaddressed,
    '/action-center/completed': summary?.completed,
  };

  return (
    <>
      <h1>Action Center</h1>
      <p className="text-muted">What was asked of whom, and whether it has happened.</p>
      <ChaseRules />

      <div className="action-center-screens">
        {TABS.map((tab) => (
          <Link key={tab.path} to={tab.path}
                className={here === tab.path ? 'is-selected' : undefined}>
            {tab.label}
            {counts[tab.path] !== undefined ? ` (${counts[tab.path]})` : ''}
          </Link>
        ))}
      </div>

      {here === '/action-center' && (
        <ActionExplorer status="Open" summary={summary} onChanged={reload} />
      )}
      {here === '/action-center/needs-you' && <NeedsYourCall onChanged={reload} />}
      {here === '/action-center/completed' && (
        <CompletedPanel summary={summary} onChanged={reload} />
      )}
      {here === '/action-center/new' && <NewActionPanel />}
    </>
  );
}
