import { Link } from 'react-router';
import type { EmailCaptureStatus } from './client';

function formatSince(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatAge(hours: number): string {
  if (hours < 48) return `${Math.round(hours)} hours`;
  return `${Math.floor(hours / 24)} days`;
}

/** Says why an email count cannot be trusted, or nothing when it can.
 *
 * My Day once showed 0 emails for eight days while capture could not sign in:
 * "Nothing captured yet" read as a quiet week. A count is only shown bare when
 * capture is known to be bringing email in. */
export function CaptureNotice({ status }: { status: EmailCaptureStatus | undefined }) {
  if (!status || status.state === 'fresh' || status.state === 'nothing') return null;
  if (status.state === 'index_unavailable') {
    return (
      <div className="card my-day-capture-notice" role="status" data-state={status.state}>
        <span className="badge badge-warning">Index not ready</span>{' '}
        The vault index holds no notes right now, so My Day cannot tell whether
        there is email. It is rebuilt within seconds of the app starting —
        reload in a moment.
      </div>
    );
  }
  return (
    <div className="card my-day-capture-notice" role="alert" data-state={status.state}>
      <span className="badge badge-danger">
        No new email for {formatAge(status.age_hours ?? 0)}
      </span>{' '}
      Email capture has brought nothing into the vault since{' '}
      <strong>{status.last_captured_at ? formatSince(status.last_captured_at) : 'it started'}</strong>.
      Anything that arrived after that is missing here — capture is failing,
      not your inbox quiet. <Link to="/system-health">See System Health</Link>.
    </div>
  );
}

/** What an email count of zero honestly means, given the capture status. */
export function emptyEmailLabel(status: EmailCaptureStatus | undefined): string {
  if (status?.state === 'index_unavailable') return 'Index not ready';
  if (status?.state === 'stale') return 'Capture stalled — count unknown';
  return 'Nothing captured yet';
}
