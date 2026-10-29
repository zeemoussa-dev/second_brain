import type { MonthRow, Summary } from './client';
import { formatMonth, usd } from './format';

export function Kpis({ summary }: { summary: Summary }) {
  return (
    <div className="insight-kpis">
      <div className="card insight-kpi">
        <span className="insight-kpi-label">Last closed month</span>
        <strong>{usd(summary.last_month?.revenue)}</strong>
        <span className="text-muted">{summary.last_month ? formatMonth(summary.last_month.month) : 'none yet'}</span>
      </div>
      <div className="card insight-kpi">
        <span className="insight-kpi-label">Year to date</span>
        <strong>{usd(summary.ytd)}</strong>
        <span className="text-muted">{summary.year}</span>
      </div>
      <div className="card insight-kpi">
        <span className="insight-kpi-label">Forecast to year end</span>
        <strong>{usd(summary.forecast_year_end)}</strong>
        <span className="text-muted">actual + forecast, {summary.year}</span>
      </div>
      <div className="card insight-kpi">
        <span className="insight-kpi-label">Lifetime</span>
        <strong>{usd(summary.lifetime)}</strong>
        <span className="text-muted">actual, every year</span>
      </div>
    </div>
  );
}

export function MonthTable({ rows, showTerms = true }: { rows: MonthRow[]; showTerms?: boolean }) {
  return (
    <table className="insight-table">
      <thead>
        <tr>
          <th>Month</th>
          {showTerms ? <th>Terms</th> : null}
          <th className="num">Consumption</th>
          <th className="num">Insight revenue</th>
          <th className="num">Cumulative</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.month} className={row.kind === 'forecast' ? 'insight-forecast' : undefined}>
            <td>
              {formatMonth(row.month)}
              {row.kind === 'forecast' ? <span className="badge insight-badge">forecast</span> : null}
            </td>
            {showTerms ? <td>{row.line ?? <span className="text-muted">no terms</span>}</td> : null}
            <td className="num">
              {row.missing_consumption ? <span className="insight-warn" title="Not synced in Cost Manager">not synced</span>
                : usd(row.consumption)}
            </td>
            <td className="num">{usd(row.revenue)}</td>
            <td className="num">{usd(row.cumulative)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function Warnings({ warnings }: { warnings: string[] }) {
  if (!warnings.length) return null;
  return (
    <ul className="insight-warnings">
      {warnings.map((warning) => <li key={warning}>{warning}</li>)}
    </ul>
  );
}
