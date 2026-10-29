import { ApiError } from '../../pluginHost/api';
import { pluginSettingsLink } from '../../pluginHost/breadcrumbs';

export const PLUGIN_ID = 'core42-insight';
export const HOME_PATH = '/core42-insight';
export const REPORT_PATH = '/core42-insight/report';
export const PORTFOLIO_PATH = '/core42-insight/portfolio';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function formatMonth(month: string, short = false): string {
  const [year, number] = month.split('-');
  const name = MONTHS[Number(number) - 1] ?? month;
  return short ? `${name} ${year.slice(2)}` : `${name} ${year}`;
}

/** Insight is always USD (operator, 2026-10-18). */
export function usd(value: number | null | undefined, compact = false): string {
  if (value === null || value === undefined) return '–';
  return new Intl.NumberFormat(undefined, {
    style: 'currency', currency: 'USD', notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 1 : 0,
  }).format(value);
}

/** The backend's `detail`, rather than the raw JSON the host's ApiError carries. */
export function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const detail = JSON.parse(error.message).detail;
      if (typeof detail === 'string') return detail;
    } catch {
      // not JSON: fall through to the raw text
    }
    return error.message || `Request failed (${error.status})`;
  }
  return error instanceof Error ? error.message : String(error);
}

export function reportLink(stem?: string): string {
  return stem ? `${REPORT_PATH}?${new URLSearchParams({ customer: stem })}` : REPORT_PATH;
}

/** Settings, opened on one customer's terms when `stem` is given; `from` lets
 *  the host's trail and Save lead back to the page it was opened from. */
export function settingsLink(from?: { location: { pathname: string; search: string }; label: string },
                             stem?: string): string {
  return pluginSettingsLink(PLUGIN_ID, {
    params: stem ? { customer: stem } : undefined,
    from: from?.location, fromLabel: from?.label,
  });
}
