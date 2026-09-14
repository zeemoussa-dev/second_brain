import { Link, useLocation } from 'react-router';

// Cockpit is a framework component (ADR-022), so it cannot name the screen
// that opened it -- the opening screen passes the way back in router state
// instead (BUG-063 seam). Opened without that state, there is no back link.
interface BackLinkState {
  backTo?: string;
  backLabel?: string;
}

export function CockpitBackLink() {
  const state = (useLocation().state ?? {}) as BackLinkState;
  // Only an in-app path: a protocol-relative "//host" would leave the app.
  if (!state.backTo || !state.backTo.startsWith('/') || state.backTo.startsWith('//')) {
    return null;
  }
  return (
    <p className="text-muted">
      <Link className="text-muted" to={state.backTo}>
        &larr; {state.backLabel ?? 'Back'}
      </Link>
    </p>
  );
}
