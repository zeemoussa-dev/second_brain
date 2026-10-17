import { Link } from 'react-router';

/** One step in the trail. `to` omitted makes it plain text -- the page you are
 *  on, and any step that is not a real place to go back to. */
export interface Crumb {
  label: string;
  to?: string;
}

export interface BreadcrumbsProps {
  items: readonly Crumb[];
}

/**
 * The trail of where you are, rendered above a page's `h1`.
 *
 * Exists because a screen reached from somewhere else had no way back
 * (2026-10-17): opening a customer's editor from an Azure Cost report landed in
 * `/settings/plugins/azure-cost-manager`, a different top-level area of the app,
 * with nothing linking back to the report. The sidebar cannot help -- Settings is
 * not where the operator was.
 *
 * The LAST item is always the current page and is never a link, even when a `to`
 * is given: a link to the page you are on reads as a way out and goes nowhere.
 */
export function Breadcrumbs({ items }: BreadcrumbsProps) {
  const trail = items.filter((item) => item.label.trim().length > 0);
  // One crumb is just the page's own name, which the `h1` under it already says.
  if (trail.length < 2) return null;

  return (
    <nav className="breadcrumbs" aria-label="Breadcrumb">
      {trail.map((item, index) => {
        const isCurrent = index === trail.length - 1;
        return (
          <span key={`${item.label}-${index}`} className="breadcrumbs-item">
            {index > 0 ? <span className="breadcrumbs-separator" aria-hidden="true">›</span> : null}
            {item.to && !isCurrent ? (
              <Link to={item.to}>{item.label}</Link>
            ) : (
              <span aria-current={isCurrent ? 'page' : undefined}>{item.label}</span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
