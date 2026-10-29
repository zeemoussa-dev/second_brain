import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { refusalText } from '../features/auth/SignInScreen';
import {
  fetchCrawlers,
  type Crawler,
  type CrawlerDefinition,
  type CrawlersView,
} from '../features/hermes-ops/client';

// "Crawlers" (operator, 2026-08-23: "Just Call the Corn Jobs Crawlers and
// Bring the stuff here") -- this page used to list Second-Brain-native
// background agents (is_background_agent === true), a concept that no
// longer has any real members since ADR-004 set every real Hermes agent
// to is_background_agent: false. Repurposed for Hermes' own real cron
// jobs -- the genuinely recurring, unattended, background-running things
// in this app now -- keeping the "Crawlers" name/route/nav slot per the
// operator's own explicit choice rather than introducing a new one.

function formatTimestamp(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

function StatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="badge">Unknown</span>;
  if (status === 'ok' || status === 'completed') return <span className="badge badge-success">{status}</span>;
  if (status === 'error' || status === 'failed') return <span className="badge badge-danger">{status}</span>;
  return <span className="badge badge-warning">{status}</span>;
}


/** How long until it next runs, in words. A timestamp alone makes you
 *  do arithmetic to answer the question you actually came with, which
 *  is "is this about to happen or did it stall". */
function whenNext(iso: string | null): string {
  if (!iso) return 'not scheduled';
  const minutes = Math.round((new Date(iso).getTime() - Date.now()) / 60000);
  if (minutes < -1) return `overdue by ${formatGap(-minutes)}`;
  if (minutes <= 1) return 'due now';
  return `in ${formatGap(minutes)}`;
}

function formatGap(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  return hours < 24 ? `${hours}h ${minutes % 60}m` : `${Math.floor(hours / 24)}d ${hours % 24}h`;
}

/** What this crawler runs, as one glanceable line.
 *
 * Named by KIND because the jobs on a real install are not one shape:
 * most run a script with no prompt at all, and a screen that only knew
 * how to show a prompt showed those as empty — which is what "I need
 * to see what's inside" was about. */
function DefinitionLine({ definition }: { definition: CrawlerDefinition }) {
  if (definition.kind === 'script') {
    return (
      <span className="crawler-definition" data-testid="crawler-definition">
        <span className="badge">script</span>
        <code>{definition.runs}</code>
      </span>
    );
  }
  if (definition.kind === 'unknown') {
    return (
      <span className="crawler-definition" data-testid="crawler-definition">
        <span className="badge badge-warning">not readable</span>
        This job runs, but nothing this app can read says what it does.
      </span>
    );
  }
  return (
    <span className="crawler-definition" data-testid="crawler-definition">
      <span className="badge">{definition.kind === 'steps' ? 'steps' : 'skill'}</span>
      <code>{definition.runs || '(no skill named)'}</code>
    </span>
  );
}


function CrawlerRow({ job }: { job: Crawler }) {
  return (
    <Link className="item-row crawler-row" to={`/crawlers/${encodeURIComponent(job.id)}`}>
      <div className="item-row-main">
        <span className="item-row-title">
          {/* The friendly name leads when there is one, and Hermes' own
              name stays visible underneath -- a label that REPLACED it
              would make a job unfindable by the name in Hermes' logs. */}
          {job.friendly_name || job.name}{' '}
          <StatusBadge status={job.state === 'scheduled' ? job.last_status : job.state} />
          {!job.enabled && <span className="badge">Disabled</span>}
          {job.tags.map((tag) => (
            <span className="badge crawler-tag" key={tag}>{tag}</span>
          ))}
        </span>
        {job.friendly_name && (
          <span className="item-row-meta mono" data-testid="crawler-real-name">{job.name}</span>
        )}
        <DefinitionLine definition={job.definition} />
        <span className="item-row-meta">
          <strong>{job.schedule_display}</strong> — next {whenNext(job.next_run_at)}{' '}
          ({formatTimestamp(job.next_run_at)}) — last ran {formatTimestamp(job.last_run_at)}
          {job.failure_streak > 0 && ` — ${job.failure_streak} failures in a row`}
        </span>
        {job.delivery_error && (
          <span className="item-row-meta crawler-delivery-error" data-testid="crawler-delivery-error">
            Delivery failed: {job.delivery_error}
          </span>
        )}
      </div>
    </Link>
  );
}

export function CrawlersPage() {
  const [view, setView] = useState<CrawlersView | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [tagFilter, setTagFilter] = useState<string>('');

  const loadJobs = () => {
    fetchCrawlers().then(
      (next) => { setView(next); setFailure(null); },
      (error) => setFailure(refusalText(error)),
    );
  };
  useEffect(loadJobs, []);

  const shown = (view?.crawlers ?? []).filter(
    (job) => tagFilter === '' || job.tags.includes(tagFilter),
  );
  // Soonest first: the question this page is open for is what is about
  // to happen, not what was created first.
  const ordered = [...shown].sort((left, right) => {
    const at = (job: Crawler) => (job.next_run_at ? new Date(job.next_run_at).getTime() : Infinity);
    return at(left) - at(right);
  });

  return (
    <>
      <h1>Crawlers</h1>
      <p className="text-muted">
        Hermes' own real cron jobs — what each one runs, when it runs, and every run's own
        report and raw log lines. The name and tags are yours; everything else is Hermes'.
      </p>
      {failure && <p className="auth-refusal" role="alert">{failure}</p>}
      {view?.annotations_unreadable && (
        <p className="auth-refusal" role="alert" data-testid="crawler-annotations-unreadable">
          Your names and tags could not be read, so every crawler is shown under its Hermes
          name: {view.annotations_unreadable}
        </p>
      )}
      <div className="card">
        <div className="crawler-toolbar">
          <button type="button" className="btn" onClick={loadJobs}>&#8635; Refresh</button>
          {/* Shown only once something is tagged. A filter over an
              empty vocabulary is a control that can do nothing. */}
          {(view?.tags.length ?? 0) > 0 && (
            <select
              className="input"
              aria-label="Filter by tag"
              data-testid="crawler-tag-filter"
              value={tagFilter}
              onChange={(event) => setTagFilter(event.target.value)}
            >
              <option value="">every crawler ({view?.crawlers.length ?? 0})</option>
              {view?.tags.map((tag) => (
                <option key={tag} value={tag}>
                  {tag} ({view.crawlers.filter((job) => job.tags.includes(tag)).length})
                </option>
              ))}
            </select>
          )}
        </div>
        {!view ? (
          <p className="text-muted">Loading...</p>
        ) : ordered.length === 0 ? (
          <div className="empty-state">
            <p className="text-muted">
              {view.crawlers.length === 0
                ? 'No cron jobs found.'
                : `No crawler is tagged "${tagFilter}".`}
            </p>
          </div>
        ) : (
          <div className="item-list">
            {ordered.map((job) => (
              <CrawlerRow key={job.id} job={job} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
