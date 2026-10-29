import { Link } from 'react-router';
import { PORTFOLIO_PATH, REPORT_PATH, settingsLink } from './format';

/** The landing page: pick a report first, then (for one customer) the customer. */
export function HomePage() {
  return (
    <div className="page insight-page">
      <header className="insight-header">
        <h1>Core42 Insight</h1>
        <Link to={settingsLink()} className="insight-header-end">Customers' Insight terms</Link>
      </header>
      <p className="text-muted">
        Insight revenue from each customer's terms -- a percentage of the month's Azure consumption, an up-front
        fee or a yearly fee -- on the consumption Azure Customer 360 synced. All figures USD.
      </p>
      <div className="insight-report-grid">
        <Link to={REPORT_PATH} className="card insight-report-card">
          <strong>Customer report</strong>
          <span className="text-muted">One customer and its affiliates: month by month, actual and forecast, cumulative.</span>
        </Link>
        <Link to={PORTFOLIO_PATH} className="card insight-report-card">
          <strong>All customers</strong>
          <span className="text-muted">Every customer's terms today, last month, year to date and forecast. Excel export.</span>
        </Link>
      </div>
    </div>
  );
}
