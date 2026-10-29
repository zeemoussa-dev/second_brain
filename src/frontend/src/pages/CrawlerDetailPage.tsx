import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { useAuth } from '../features/auth/AuthGate';
import { refusalText } from '../features/auth/SignInScreen';
import {
  fetchCrawlers,
  fetchCronRunDetail,
  fetchCronRuns,
  saveCrawlerAnnotation,
  type Crawler,
  type HermesCronExecution,
  type HermesCronRunDetail,
} from '../features/hermes-ops/client';

/** One crawler, on its own page (operator, 2026-10-24: "I need to have
 * a page with crawler").
 *
 * **A row could not hold this.** What a crawler is made of — the script
 * or the prompt it runs, its steps, its schedule, its labels and its
 * whole run history — is more than fits beside eleven siblings, and
 * cramming it there is what made "I need to see what's inside" a
 * complaint in the first place.
 *
 * **Read from the same list the index page reads.** This install has
 * twelve crawlers and the list is one request, so filtering it here
 * costs nothing and means the two pages can never disagree about what
 * a crawler is. A per-crawler endpoint would be a second shape to keep
 * in step for no gain at this size.
 *
 * **Hermes owns everything here except the name and the tags.** The
 * page says so, because a screen where some fields are editable and
 * others merely look it is a screen that invites someone to try.
 */
function formatTimestamp(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString() : '—';
}

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

function StatusBadge({ status }: { status: string | null }) {
  if (!status) return <span className="badge">Unknown</span>;
  if (status === 'ok' || status === 'completed') return <span className="badge badge-success">{status}</span>;
  if (status === 'error' || status === 'failed') return <span className="badge badge-danger">{status}</span>;
  return <span className="badge badge-warning">{status}</span>;
}

function RunDetail({ jobId, execution }: { jobId: string; execution: HermesCronExecution }) {
  const [detail, setDetail] = useState<HermesCronRunDetail | null>(null);
  const [showRawLog, setShowRawLog] = useState(false);

  useEffect(() => {
    setDetail(null);
    fetchCronRunDetail(jobId, execution.id).then(setDetail);
  }, [jobId, execution.id]);

  if (!detail) return <p className="text-muted">Loading run detail…</p>;

  return (
    <div className="crawler-run-detail">
      {detail.report_markdown ? (
        <pre className="mono crawler-pre">{detail.report_markdown}</pre>
      ) : (
        <p className="text-muted">
          No per-run report for this run — it may still be running, or never wrote one.
        </p>
      )}
      <button type="button" className="btn" onClick={() => setShowRawLog((v) => !v)}>
        {showRawLog ? 'Hide' : 'Show'} raw agent.log lines ({detail.log_lines.length})
      </button>
      {showRawLog && (
        <pre className="mono crawler-pre">
          {detail.log_lines.join('\n') || '(no matching log lines found)'}
        </pre>
      )}
    </div>
  );
}

export function CrawlerDetailPage() {
  const { jobId = '' } = useParams();
  const { may } = useAuth();
  const canLabel = may('manage_hermes');

  const [crawler, setCrawler] = useState<Crawler | null | 'missing'>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [runs, setRuns] = useState<HermesCronExecution[] | null>(null);
  const [openRun, setOpenRun] = useState<HermesCronExecution | null>(null);
  const [nameDraft, setNameDraft] = useState('');
  const [tagsDraft, setTagsDraft] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const view = await fetchCrawlers();
      const found = view.crawlers.find((candidate) => candidate.id === jobId);
      if (!found) { setCrawler('missing'); return; }
      setCrawler(found);
      setNameDraft(found.friendly_name);
      setTagsDraft(found.tags.join(', '));
      setFailure(null);
    } catch (error) {
      setFailure(refusalText(error));
    }
  }, [jobId]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { fetchCronRuns(jobId).then(setRuns, () => setRuns([])); }, [jobId]);

  async function saveLabel() {
    setSaving(true);
    try {
      await saveCrawlerAnnotation(
        jobId, nameDraft, tagsDraft.split(',').map((tag) => tag.trim()).filter(Boolean),
      );
      await load();
    } catch (error) {
      setFailure(refusalText(error));
    } finally {
      setSaving(false);
    }
  }

  if (failure && crawler === null) {
    return <><h1>Crawler</h1><p className="auth-refusal" role="alert">{failure}</p></>;
  }
  if (crawler === 'missing') {
    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/crawlers">&larr; Crawlers</Link></p>
        <h1>No such crawler</h1>
        <p className="auth-note">
          Hermes has no cron job with id <code>{jobId}</code> on this install. It may have been
          deleted, or it belongs to a profile this page does not read.
        </p>
      </>
    );
  }
  if (crawler === null) return <><h1>Crawler</h1><p>Reading this crawler…</p></>;

  const { definition } = crawler;

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/crawlers">&larr; Crawlers</Link></p>
      <h1>
        {crawler.friendly_name || crawler.name}{' '}
        <StatusBadge status={crawler.state === 'scheduled' ? crawler.last_status : crawler.state} />
        {!crawler.enabled && <span className="badge">Disabled</span>}
      </h1>
      <p className="auth-note">
        <code>{crawler.name}</code> · id <code>{crawler.id}</code>
        {crawler.tags.map((tag) => (
          <span className="badge crawler-tag" key={tag} style={{ marginLeft: 'var(--space-2)' }}>{tag}</span>
        ))}
      </p>

      {failure && <p className="auth-refusal" role="alert">{failure}</p>}

      <section>
        <h2>When it runs</h2>
        <table className="settings-table">
          <tbody>
            <tr><td>Schedule</td><td><strong>{crawler.schedule_display}</strong></td></tr>
            <tr>
              <td>Next run</td>
              <td data-testid="crawler-next-run">
                <strong>{whenNext(crawler.next_run_at)}</strong> — {formatTimestamp(crawler.next_run_at)}
              </td>
            </tr>
            <tr><td>Last run</td><td>{formatTimestamp(crawler.last_run_at)}</td></tr>
            <tr><td>Runs completed</td><td>{crawler.repeat_completed}</td></tr>
            <tr><td>Delivers to</td><td>{crawler.deliver || '—'}</td></tr>
          </tbody>
        </table>
        {crawler.failure_streak > 0 && (
          <p className="auth-refusal" role="alert">
            {crawler.failure_streak} failures in a row.
            {crawler.last_error ? ` Last error: ${crawler.last_error}` : ''}
          </p>
        )}
        {/* Hermes keeps a delivery failure apart from `last_error`, so
            without this a job reading `delivery_failed` has its reason
            nowhere on the screen at all. */}
        {crawler.delivery_error && (
          <p className="auth-refusal" role="alert" data-testid="crawler-delivery-error">
            Delivery failed: {crawler.delivery_error}
          </p>
        )}
      </section>

      <section>
        <h2>What it runs</h2>
        {definition.kind === 'script' && (
          <p data-testid="crawler-definition">
            A script, with no agent in the loop: <code>{definition.runs}</code>
          </p>
        )}
        {definition.kind === 'unknown' && (
          <p className="auth-note" data-testid="crawler-definition">
            This job runs on its schedule, but neither Hermes' job record nor its own file says
            what it does. That is a gap in what this app can read, not an empty job.
          </p>
        )}
        {(definition.kind === 'steps' || definition.kind === 'instruction') && (
          <p data-testid="crawler-definition">
            An agent run using the skill <code>{definition.runs || '(none named)'}</code>
          </p>
        )}
        {definition.skills.length > 1 && (
          <p className="auth-note">Skills: {definition.skills.map((s) => <code key={s}>{s} </code>)}</p>
        )}
        {crawler.model && <p className="auth-note">Model at last snapshot: <code>{crawler.model}</code></p>}

        {definition.steps.length > 0 ? (
          <>
            <h3>Its steps</h3>
            <ol className="crawler-steps" data-testid="crawler-steps">
              {definition.steps.map((step) => (
                <li key={step.number}>
                  <span className="crawler-step-number">{step.number}</span>
                  <span>{step.says}</span>
                </li>
              ))}
            </ol>
          </>
        ) : (
          definition.says && (
            <p className="auth-note">
              This one does not spell its work out as numbered steps — its instruction is below,
              as written.
            </p>
          )
        )}

        {definition.says && (
          <>
            <h3>In full</h3>
            <pre className="mono crawler-pre" data-testid="crawler-prompt">{definition.says}</pre>
          </>
        )}
      </section>

      <section>
        <h2>Name and tags</h2>
        <p className="auth-note">
          Yours, not Hermes'. Everything else on this page is Hermes' own and is shown as it is.
        </p>
        {canLabel ? (
          <div className="crawler-label-editor">
            <input
              className="input"
              placeholder="a friendly name"
              aria-label="Friendly name"
              data-testid="crawler-name"
              value={nameDraft}
              onChange={(event) => setNameDraft(event.target.value)}
            />
            <input
              className="input"
              placeholder="tags, comma separated — e.g. indexes"
              aria-label="Tags"
              data-testid="crawler-tags"
              value={tagsDraft}
              onChange={(event) => setTagsDraft(event.target.value)}
            />
            <button type="button" className="btn" disabled={saving} onClick={() => void saveLabel()}>
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        ) : (
          <p className="auth-note">Naming and tagging a crawler needs an Admin.</p>
        )}
      </section>

      <section>
        <h2>Run history</h2>
        {!runs ? (
          <p className="text-muted">Loading run history…</p>
        ) : runs.length === 0 ? (
          <p className="auth-note">No runs recorded yet.</p>
        ) : (
          <div className="item-list" data-testid="crawler-runs">
            {runs.map((run) => (
              <div key={run.id}>
                <div
                  className="item-row"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setOpenRun(openRun?.id === run.id ? null : run)}
                >
                  <div className="item-row-main">
                    <span className="item-row-title">
                      <StatusBadge status={run.status} />{' '}
                      <span className="mono">{formatTimestamp(run.started_at)}</span>
                    </span>
                    <span className="item-row-meta">
                      {run.finished_at
                        ? `Finished ${formatTimestamp(run.finished_at)}`
                        : 'Still running, or never recorded a finish'}
                      {run.error && ` — ${run.error}`}
                    </span>
                  </div>
                </div>
                {openRun?.id === run.id && <RunDetail jobId={crawler.id} execution={run} />}
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
