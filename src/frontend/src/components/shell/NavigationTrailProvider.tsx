import { useEffect, useRef, useState, type ReactNode } from 'react';
import { useLocation, useNavigationType } from 'react-router';
import { TrailContext, labelFor, type TrailEntry } from './navigationTrail';

/** Mirrors the router's own history stack, so a Back control can name the page
 * it would return to. See navigationTrail.ts for why this exists. */
export function NavigationTrail({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigationType = useNavigationType();
  const [previous, setPrevious] = useState<TrailEntry | null>(null);
  // React Router exposes the current entry only, so "the one before" has to be
  // kept here.
  const stack = useRef<TrailEntry[]>([]);
  const here = useRef<TrailEntry | null>(null);

  useEffect(() => {
    const entry: TrailEntry = {
      to: location.pathname + location.search,
      label: labelFor(location.pathname),
    };

    if (here.current && here.current.to !== entry.to) {
      if (navigationType === 'POP') {
        // Back (or Forward) -- the page we were on is no longer behind us.
        stack.current.pop();
      } else if (navigationType === 'PUSH') {
        stack.current.push(here.current);
      }
      // REPLACE deliberately does nothing: a filter rewriting its own URL is
      // not a journey, and treating it as one would make Back undo a click on
      // a dropdown rather than leave the screen (ADR-041 writes filters with
      // replace for exactly that reason).
    }

    here.current = entry;
    setPrevious(stack.current.length ? stack.current[stack.current.length - 1] : null);
  }, [location, navigationType]);

  return <TrailContext.Provider value={previous}>{children}</TrailContext.Provider>;
}
