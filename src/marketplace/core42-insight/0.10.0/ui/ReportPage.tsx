import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router';
import { apiUrl } from '../../pluginHost/api';
import { Breadcrumbs } from '../../pluginHost/breadcrumbs';
import { useUrlState } from '../../pluginHost/state';
import { RevenueChart } from './charts';
import { fetchReport, reportExportPath, type Report } from './client';
import { CustomerChooser } from './CustomerChooser';
import { HOME_PATH, REPORT_PATH, errorText, reportLink, settingsLink, usd } from './format';
import { Kpis, MonthTable, Warnings } from './parts';

export function ReportPage() {
  const location = useLocation();
  const [stem] = useUrlState('customer');
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setReport(null);
    setError(null);
    if (stem) fetchReport(stem).then(setReport, (failure) => setError(errorText(failure)));
  }, [stem]);

  const hasTerms = report?.members.some((member) => member.terms.length > 0);
  return (
    <div className="page insight-page">
      <Breadcrumbs items={[
        { label: 'Core42 Insight', to: HOME_PATH },
        { label: 'Customer report', to: REPORT_PATH },
        ...(report?.parent ? [{ label: report.parent, to: reportLink(report.parent) }] : []),
        ...(stem ? [{ label: report?.name ?? stem }] : []),
      ]} />
      <header className="insight-header">
        <h1>{stem ? report?.name ?? stem : 'Customer report'}</h1>
        {report ? (
          <>
            <Link className="insight-header-end"
                  to={settingsLink({ location, label: report.name }, report.stem)}>Edit terms</Link>
            {report.cost_route ? <Link to={report.cost_route}>Azure consumption</Link> : null}
            {hasTerms ? <a className="btn" href={apiUrl(reportExportPath(report.stem))}>Export to Excel</a> : null}
          </>
        ) : null}
      </header>
      {!stem ? <CustomerChooser /> : null}
      {error ? <div className="insight-error">{error}</div> : null}
      {stem && !report && !error ? <p className="text-muted">Loading…</p> : null}
      {report && !hasTerms ? (
        <p className="empty-state">
          No Insight terms on this customer yet.{' '}
          <Link to={settingsLink({ location, label: report.name }, report.stem)}>Set them up</Link>.
        </p>
      ) : null}
      {report && hasTerms ? (
        <>
          <Warnings warnings={report.warnings} />
          {report.affiliates_reported_alone?.length ? (
            <p className="text-muted">
              Its affiliates each signed their own MACC, so they are reported on their own:{' '}
              {report.affiliates_reported_alone.map((affiliate, index) => (
                <span key={affiliate.stem}>{index ? ', ' : ''}
                  <Link to={reportLink(affiliate.stem)}>{affiliate.name}</Link></span>
              ))}.
            </p>
          ) : null}
          <Kpis summary={report.summary} />
          <section className="card insight-section">
            <RevenueChart rows={report.rows} />
          </section>
          {report.members.length > 1 ? (
            <section className="insight-section">
              <h2>By customer</h2>
              <table className="insight-table">
                <thead>
                  <tr><th>Customer</th><th>Terms today</th><th className="num">Year to date</th>
                    <th className="num">Forecast to year end</th><th className="num">Lifetime</th></tr>
                </thead>
                <tbody>
                  {report.members.map((member) => {
                    const today = member.rows.find((row) => row.month === report.current_month);
                    return (
                      <tr key={member.stem}>
                        <td>{member.stem === report.stem ? member.name
                          : <Link to={reportLink(member.stem)}>{member.name}</Link>}</td>
                        <td>
                          {today?.line ?? <span className="text-muted">none</span>}
                          {member.inherited_from && today?.line ? <span className="text-muted"> (from {member.inherited_from})</span> : null}
                        </td>
                        <td className="num">{usd(member.summary.ytd)}</td>
                        <td className="num">{usd(member.summary.forecast_year_end)}</td>
                        <td className="num">{usd(member.summary.lifetime)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </section>
          ) : null}
          <section className="insight-section">
            <h2>Month by month</h2>
            <MonthTable rows={report.rows} showTerms={report.members.length === 1} />
          </section>
        </>
      ) : null}
    </div>
  );
}
