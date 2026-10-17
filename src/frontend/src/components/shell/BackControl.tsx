// The way back, on every screen (operator, 2026-10-17: clicking an email in
// My Day landed on the note with no way back).
//
// NOT ADR-060: that is the breadcrumbs decision, a different mechanism for
// the same complaint. The operator kept BOTH (2026-10-18): this is the
// one-step back every screen gets for free; breadcrumbs are the named trail
// a plugin renders deliberately. ADR-060 holds the boundary.
//
// It lives in the shell rather than on each page for two reasons: a page added
// tomorrow gets it without remembering to, and a plugin's screen gets it
// without the Plugin API having to grow a component for it.

import { useNavigate } from 'react-router';
import { usePreviousPage } from './navigationTrail';

export function BackControl() {
  const navigate = useNavigate();
  const previous = usePreviousPage();

  // A cold load -- opening a link straight into a note -- has nowhere to go
  // back to, and an arrow that does nothing is worse than no arrow.
  if (!previous) return null;

  return (
    <nav className="back-control" aria-label="Go back">
      {/* navigate(-1), not a Link to the path: it re-uses the history entry,
          so Forward still works and the page is restored rather than remounted
          from scratch. The path is only used to NAME where that goes. */}
      <button type="button" className="back-control-button" onClick={() => navigate(-1)}>
        <span aria-hidden="true">&larr;</span> {previous.label}
      </button>
    </nav>
  );
}
