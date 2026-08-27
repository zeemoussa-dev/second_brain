import { useEffect, useRef, useState } from 'react';
import type { BootStatus, BootStageId } from './bootApiClient';
import { getBootStatus, retryBoot } from './bootApiClient';

const STAGE_LABELS: Record<BootStageId, string> = {
  checking_hermes: 'Checking Hermes',
  loading_sections: 'Loading Sections',
  loading_agents: 'Loading agents',
  loading_skills: 'Getting skills',
  loading_providers: 'Loading providers',
};

const POLL_MS = 1000;
// 2 consecutive missed polls (~2s) before declaring the backend down --
// avoids a false-positive flicker on one single dropped request.
const UNREACHABLE_AFTER_FAILURES = 2;

function StageIcon({ status }: { status: BootStatus['stages'][number]['status'] }) {
  if (status === 'done') return <span className="material-symbols-outlined boot-stage-icon boot-stage-icon-done">check_circle</span>;
  if (status === 'failed') return <span className="material-symbols-outlined boot-stage-icon boot-stage-icon-failed">error</span>;
  if (status === 'in_progress') return <span className="material-symbols-outlined boot-stage-icon boot-stage-icon-active boot-spin">progress_activity</span>;
  return <span className="material-symbols-outlined boot-stage-icon boot-stage-icon-pending">radio_button_unchecked</span>;
}

function StageList({ status }: { status: BootStatus }) {
  return (
    <ol className="boot-stage-list">
      {status.stages.map((stage) => (
        <li key={stage.id} className={`boot-stage boot-stage-${stage.status}`}>
          <StageIcon status={stage.status} />
          <span className="boot-stage-label">{STAGE_LABELS[stage.id]}</span>
        </li>
      ))}
    </ol>
  );
}

function ErrorPanel({ status, onRetry, retrying }: { status: BootStatus; onRetry: () => void; retrying: boolean }) {
  if (!status.error) return null;
  return (
    <div className="boot-error">
      <p className="boot-error-message">{status.error.message}</p>
      <p className="boot-error-file">{status.error.file}</p>
      <button type="button" className="boot-retry-button" onClick={onRetry} disabled={retrying}>
        {retrying ? 'Retrying…' : 'Fix the file, then retry'}
      </button>
    </div>
  );
}

/** REQ-SB-80 -- one status model (GET /boot-status), two presentations:
 * a full-screen block for cold boot (nothing rendered underneath yet to
 * show instead), and a small corner banner for a hot-reload that happens
 * after the app is already up. A cold-boot failure blocks; a hot-reload
 * failure surfaces prominently but never yanks away the already-working
 * app underneath it (operator: "Fail Loud so I can fix or remove", not
 * "take away what I was just looking at"). */
export function BootGate({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<BootStatus | null>(null);
  const [retrying, setRetrying] = useState(false);
  // Distinct from `status.state` -- that field describes the LAST
  // successfully-fetched boot status (which can go stale the moment the
  // backend actually stops answering). This tracks the poll loop's own
  // connectivity, independent of whatever status it last managed to read
  // (operator: "I need it to tell me if the backend is down").
  const [backendUnreachable, setBackendUnreachable] = useState(false);
  const everReadyRef = useRef(false);
  const failureStreakRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        const next = await getBootStatus();
        if (cancelled) return;
        failureStreakRef.current = 0;
        setBackendUnreachable(false);
        setStatus(next);
      } catch {
        if (cancelled) return;
        failureStreakRef.current += 1;
        if (failureStreakRef.current >= UNREACHABLE_AFTER_FAILURES) setBackendUnreachable(true);
        // `status` itself is deliberately left untouched (stale, not
        // cleared) -- the post-ready banner below reads `backendUnreachable`
        // for connectivity and the last-known `status` for everything else.
      }
    }
    poll();
    const interval = setInterval(poll, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  async function handleRetry() {
    setRetrying(true);
    try {
      setStatus(await retryBoot());
    } finally {
      setRetrying(false);
    }
  }

  if (status?.state === 'ready') everReadyRef.current = true;

  // Cold boot (or the very first load, before we've heard from the
  // backend at all) -- block entry into the app entirely.
  if (!everReadyRef.current) {
    return (
      <div className="boot-screen">
        <div className="boot-screen-panel">
          <p className="boot-screen-eyebrow">Second Brain</p>
          <h1 className="boot-screen-title">
            {status?.state === 'failed' ? 'Boot failed' : 'Starting up'}
          </h1>
          {status ? (
            <StageList status={status} />
          ) : (
            <p className="boot-screen-waiting">
              {backendUnreachable ? "Backend isn't responding — make sure it's running." : 'Connecting to backend…'}
            </p>
          )}
          {status?.state === 'failed' && <ErrorPanel status={status} onRetry={handleRetry} retrying={retrying} />}
        </div>
      </div>
    );
  }

  // Already up at least once -- a later hot-reload (in progress or
  // failed) shows as a small, non-blocking banner over the real app, and
  // the backend going fully unreachable (crash, killed process, etc.)
  // shows as its own persistent top banner -- independent signals, both
  // can theoretically apply, neither blocks the already-rendered app.
  const showBanner = status && status.state !== 'ready';
  return (
    <>
      {children}
      {backendUnreachable && (
        <>
          {/* Dims AND blocks interaction with the already-rendered app
              underneath -- every click it would trigger just fails
              anyway with the backend down, so this stops the operator
              acting on a UI that can't actually do anything right now
              (operator: "add a dimmed layer on top... so I can't touch
              it"). No onClick handler needed -- an unstyled div still
              intercepts pointer events from whatever's stacked below it. */}
          <div className="backend-down-overlay" />
          <div className="backend-down-banner" role="alert">
            <span className="material-symbols-outlined boot-spin">progress_activity</span>
            <span>Backend is unreachable — retrying…</span>
          </div>
        </>
      )}
      {showBanner && (
        <div className={`boot-banner boot-banner-${status.state}`}>
          {status.state === 'booting' ? (
            <>
              <span className="material-symbols-outlined boot-spin">progress_activity</span>
              <span>{status.current_stage ? STAGE_LABELS[status.current_stage] : 'Reloading…'}</span>
            </>
          ) : (
            <>
              <span className="material-symbols-outlined">error</span>
              <span className="boot-banner-text">
                Data layer reload failed: {status.error?.message}
                <span className="boot-banner-file">{status.error?.file}</span>
              </span>
              <button type="button" className="boot-retry-button boot-retry-button-compact" onClick={handleRetry} disabled={retrying}>
                {retrying ? 'Retrying…' : 'Retry'}
              </button>
            </>
          )}
        </div>
      )}
    </>
  );
}
