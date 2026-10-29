import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router';
import { apiUrl } from '../../pluginHost/api';
import { Breadcrumbs } from '../../pluginHost/breadcrumbs';
import { RevenueChart } from './charts';
import { fetchPortfolio, portfolioExportPath, type Portfolio } from './client';
import { HOME_PATH, errorText, reportLink, settingsLink, usd } from './format';
import { Kpis, MonthTable, Warnings } from './parts';

export function PortfolioPage() {
  const location = useLocation();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetchPortfolio().then(setPortfolio, (failure) => setError(errorText(failure))); }, []);

  return (
    <div className="page insight-page">
      <Breadcrumbs items={[{ label: 'Core42 Insight', to: HOME_PATH }, { label: 'All customers' }]} />
      <header className="insight-header">
        <h1>All customers</h1>
        <Link className="insight-header-end" to={settingsLink({ location, label: 'All customers' })}>Customers' Insight terms</Link>
        {portfolio?.customers.length ? <a className="btn" href={apiUrl(portfolioExportPath())}>Export to Excel</a> : null}
      </header>
      {error ? <div className="insight-error">{error}</div> : null}
      {!portfolio && !error ? <p className="text-muted">Loading…</p> : null}
      {portfolio && portfolio.customers.length === 0 ? (
        <p className="empty-state">No customer has Insight terms yet. <Link to={settingsLink({ location, label: 'All customers' })}>Set them up</Link>.</p>
      ) : null}
      {portfolio && portfolio.customers.length ? (
        <>
          <Warnings warnings={portfolio.warnings} />
          <Kpis summary={portfolio.totals} />
          <section className="insight-section">
            <table className="insight-table">
              <thead>
                <tr>
                  <th>Customer</th><th>Terms today</th><th className="num">Last month</th>
                  <th className="num">Year to date</th>
                  <th className="num">Forecast to year end</th><th className="num">Lifetime</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.customers.map((row) => (
                  <tr key={row.stem} className={row.parent ? 'insight-affiliate' : undefined}>
                    <td><Link to={reportLink(row.stem)}>{row.name}</Link></td>
                    <td>
                      {row.in_force ?? <span className="text-muted">none today</span>}
                      {row.inherited_from && row.in_force ? <span className="text-muted"> (from {row.inherited_from})</span> : null}
                    </td>
                    <td className="num">{usd(row.summary.last_month?.revenue)}</td>
                    <td className="num">{usd(row.summary.ytd)}</td>
                    <td className="num">{usd(row.summary.forecast_year_end)}</td>
                    <td className="num">{usd(row.summary.lifetime)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className="card insight-section">
            <RevenueChart rows={portfolio.months} />
          </section>
          <section className="insight-section">
            <h2>Month by month, all customers</h2>
            <MonthTable rows={portfolio.months} showTerms={false} />
          </section>
        </>
      ) : null}
    </div>
  );
}
