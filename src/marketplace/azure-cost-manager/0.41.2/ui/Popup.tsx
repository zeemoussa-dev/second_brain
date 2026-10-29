import { useEffect, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

/** Details over the page, never pushed into it (operator, 2026-10-23: "why not a popup
 *  with a close button ... same goes for everything, much better with all drill-downs").
 *  Rendered on the body, so a table or a scrolled card cannot clip it; Close, Escape or a
 *  click outside leaves the page exactly where it was. */
export function Popup({ kicker, title, onClose, children }: {
  kicker?: string; title: ReactNode; onClose: () => void; children: ReactNode;
}) {
  const panel = useRef<HTMLElement>(null);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [onClose]);

  // Opening something else inside the popup starts it from its top.
  useEffect(() => { panel.current?.scrollTo({ top: 0 }); }, [title]);

  return createPortal(
    <div className="azure-cost-drill-backdrop" onClick={onClose}>
      <section ref={panel} className="card azure-cost-card azure-cost-drill" role="dialog" aria-modal="true"
               aria-label={typeof title === 'string' ? title : kicker} onClick={(event) => event.stopPropagation()}>
        <header className="azure-cost-drill-header">
          <div>
            {kicker ? <span className="azure-cost-kpi-label">{kicker}</span> : null}
            <h3>{title}</h3>
          </div>
          <button type="button" className="btn btn-ghost" onClick={onClose} aria-label="Close">Close</button>
        </header>
        {children}
      </section>
    </div>,
    document.body,
  );
}
