import { useEffect, useState } from 'react';
import {
  fetchCronJobs,
  fetchCronRunDetail,
  fetchCronRuns,
  type HermesCronExecution,
  type HermesCronJob,
  type HermesCronRunDetail,
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

function RunDetailPanel({ jobId, execution }: { jobId: string; execution: HermesCronExecution }) {
  const [detail, setDetail] = useState<HermesCronRunDetail | null>(null);
  const [showRawLog, setShowRawLog] = useState(false);

  useEffect(() => {
    setDetail(null);
    fetchCronRunDetail(jobId, execution.id).then(setDetail);
  }, [jobId, execution.id]);

  if (!detail) return <p className="text-muted">Loading run detail...</p>;

  return (
    <div style={{ marginTop: 'var(--space-2)', paddingLeft: 'var(--space-4)', borderLeft: '2px solid var(--color-border)' }}>
      {detail.report_markdown ? (
        <pre
          className="mono"
          style={{
            whiteSpace: 'pre-wrap',
            fontSize: 'var(--font-size-sm)',
            maxHeight: '320px',
            overflowY: 'auto',
            background: 'var(--color-surface-muted)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          {detail.report_markdown}
        </pre>
      ) : (
        <p className="text-muted">No per-run report found for this run (it may still be running, or never wrote one).</p>
      )}
      <button type="button" className="btn" style={{ marginTop: 'var(--space-2)' }} onClick={() => setShowRawLog((v) => !v)}>
        {showRawLog ? 'Hide' : 'Show'} raw agent.log lines ({detail.log_lines.length})
      </button>
      {showRawLog && (
        <pre
          className="mono"
          style={{
            whiteSpace: 'pre-wrap',
            fontSize: 'var(--font-size-xs)',
            maxHeight: '240px',
            overflowY: 'auto',
            background: 'var(--color-surface-muted)',
            padding: 'var(--space-3)',
            borderRadius: 'var(--radius-sm)',
            marginTop: 'var(--space-2)',
          }}
        >
          {detail.log_lines.join('\n') || '(no matching log lines found)'}
        </pre>
      )}
    </div>
  );
}

function CronJobRow({ job }: { job: HermesCronJob }) {
  const [expanded, setExpanded] = useState(false);
  const [runs, setRuns] = useState<HermesCronExecution[] | null>(null);
  const [selectedRun, setSelectedRun] = useState<HermesCronExecution | null>(null);

  const toggle = () => {
    setExpanded((v) => !v);
    if (!runs) fetchCronRuns(job.id).then(setRuns);
  };

  return (
    <div className="item-row" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
      <div className="item-row-main" style={{ cursor: 'pointer' }} onClick={toggle}>
        <span className="item-row-title">
          {job.name} <StatusBadge status={job.state === 'scheduled' ? job.last_status : job.state} />
          {!job.enabled && <span className="badge">Disabled</span>}
        </span>
        <span className="item-row-meta">
          {job.schedule_display} — skill: <span className="mono">{job.skill}</span> — next run:{' '}
          {formatTimestamp(job.next_run_at)} — last run: {formatTimestamp(job.last_run_at)}
          {job.failure_streak > 0 && ` — ${job.failure_streak} failures in a row`}
        </span>
      </div>
      {expanded && (
        <div style={{ marginTop: 'var(--space-2)', paddingLeft: 'var(--space-4)' }}>
          {!runs ? (
            <p className="text-muted">Loading run history...</p>
          ) : runs.length === 0 ? (
            <p className="text-muted">No runs recorded yet.</p>
          ) : (
            <div className="item-list">
              {runs.map((run) => (
                <div key={run.id}>
                  <div
                    className="item-row"
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedRun(selectedRun?.id === run.id ? null : run)}
                  >
                    <div className="item-row-main">
                      <span className="item-row-title">
                        <StatusBadge status={run.status} />{' '}
                        <span className="mono" style={{ fontSize: 'var(--font-size-sm)' }}>{formatTimestamp(run.started_at)}</span>
                      </span>
                      <span className="item-row-meta">
                        {run.finished_at
                          ? `Finished ${formatTimestamp(run.finished_at)}`
                          : 'Still running / did not record a finish time'}
                        {run.error && ` — ${run.error}`}
                      </span>
                    </div>
                  </div>
                  {selectedRun?.id === run.id && <RunDetailPanel jobId={job.id} execution={run} />}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function CrawlersPage() {
  const [jobs, setJobs] = useState<HermesCronJob[] | null>(null);

  const loadJobs = () => {
    fetchCronJobs().then(setJobs);
  };
  useEffect(loadJobs, []);

  return (
    <>
      <h1>Crawlers</h1>
      <p className="text-muted">
        Hermes' own real cron jobs — schedule, current state, and every
        run's own linked report + matching raw log lines, so you can see
        what a background run actually did.
      </p>
      <div className="card">
        <button type="button" className="btn" style={{ marginBottom: 'var(--space-2)' }} onClick={loadJobs}>
          &#8635; Refresh
        </button>
        {!jobs ? (
          <p className="text-muted">Loading...</p>
        ) : jobs.length === 0 ? (
          <div className="empty-state">
            <p className="text-muted">No cron jobs found.</p>
          </div>
        ) : (
          <div className="item-list">
            {jobs.map((job) => (
              <CronJobRow key={job.id} job={job} />
            ))}
          </div>
        )}
      </div>
    </>
  );
}
