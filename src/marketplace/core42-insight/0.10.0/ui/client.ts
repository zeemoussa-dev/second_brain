import { ApiError, apiFetch } from '../../pluginHost/api';

// The host mounts this plugin's backend under /plugins/<plugin-id>/.
const BASE = '/plugins/core42-insight';

export type Model = 'percentage' | 'upfront' | 'yearly';

/** One instalment of an up-front fee (operator, 2026-10-18). */
export interface Payment {
  date: string;
  amount?: number;
  note?: string;
}

export interface TermLine {
  model: Model;
  start: string;
  end?: string;
  percent?: number;
  include_marketplace?: boolean;
  subtract_credits?: boolean;
  amount?: number;
  payments?: Payment[];
  note?: string;
}


/** The agreement Insight is attached to (MACC, EA commitment, ...). */
export interface Agreement {
  type: string | null;
  amount: number | null;
  currency: string | null;
  start: string | null;
  end: string | null;
  include_marketplace?: boolean;
  subtract_credits?: boolean;
}

export type CustomerStatus = 'active' | 'inherited' | 'ended' | 'no-terms' | 'unreadable';

/** A customer screen row as the fast list gives it: who, and how they nest. */
export interface ListedCustomer {
  /** The customer's key: its note's stem, or `cm:<id>` when it has no Customer note. */
  stem: string;
  name: string;
  has_note: boolean;
  parent: string | null;
  affiliates: string[];
}

/** A row's figures, fetched on their own after the list (lazy loading, 2026-10-18). */
export interface CustomerDetail {
  stem: string;
  name: string;
  has_note: boolean;
  currency: string | null;
  has_terms: boolean;
  terms_error: string | null;
  /** The parent whose percentage it follows, having no terms of its own. */
  inherited_from: string | null;
  in_force: string | null;
  model: Model | null;
  agreement: Agreement | null;
  /** The parent whose agreement covers it, when it signs none of its own and its parent's affiliates roll up. */
  agreement_from?: string | null;
  summary: Summary | null;
  recent: { month: string; revenue: number }[];
  mom_pct: number | null;
  status: CustomerStatus;
}

export type InsightCustomer = ListedCustomer & CustomerDetail;

export interface CustomerTerms {
  stem: string;
  name: string;
  currency: string | null;
  has_note: boolean;
  terms: TermLine[];
  inherited_from: string | null;
  inherited: TermLine[];
  note: string;
  error: string | null;
  agreement: Agreement | null;
  outside_agreement: string[];
  models: { id: Model; label: string }[];
}

export interface MonthRow {
  month: string;
  kind: 'actual' | 'forecast';
  model?: Model | null;
  line?: string | null;
  consumption: number | null;
  revenue: number;
  cumulative?: number;
  missing_consumption: boolean;
}

export interface Summary {
  year: string;
  last_month: { month: string; revenue: number } | null;
  ytd: number;
  lifetime: number;
  forecast_year_end: number;
  forecast_total: number;
}

export interface Member {
  stem: string;
  name: string;
  has_note: boolean;
  inherited_from: string | null;
  currency: string | null;
  terms: TermLine[];
  rows: MonthRow[];
  summary: Summary;
  warnings: string[];
  cost_route: string | null;
}

export interface Report {
  stem: string;
  name: string;
  current_month: string;
  parent: string | null;
  members: Member[];
  rows: MonthRow[];
  summary: Summary;
  warnings: string[];
  cost_route: string | null;
  /** Affiliates that signed their own MACC: not in this report, each has its own. */
  affiliates_reported_alone?: { stem: string; name: string }[];
}

export interface PortfolioRow {
  stem: string;
  name: string;
  parent: string | null;
  inherited_from: string | null;
  in_force: string | null;
  model: Model | null;
  summary: Summary;
}

export interface Portfolio {
  current_month: string;
  year: string;
  customers: PortfolioRow[];
  totals: Summary;
  months: MonthRow[];
  warnings: string[];
}

export interface InsightSettings {
  sources: { entities: boolean; cost_manager: boolean };
}

const stemQuery = (stem: string) => `stem=${encodeURIComponent(stem)}`;

/** A read that waits out a backend reload: for some seconds after one the vault is
 *  still loading and the backend answers 503 -- "try again", never "no terms". */
async function whenVaultReady<T>(read: () => Promise<T>, tries = 6, waitMs = 5000): Promise<T> {
  for (let attempt = 1; ; attempt += 1) {
    try {
      return await read();
    } catch (failure) {
      if (!(failure instanceof ApiError && failure.status === 503) || attempt >= tries) throw failure;
      await new Promise((resolve) => setTimeout(resolve, waitMs));
    }
  }
}

export const fetchCustomerList = () => apiFetch<ListedCustomer[]>(`${BASE}/customer-list`);
export const fetchCustomerRow = (stem: string) => apiFetch<CustomerDetail>(`${BASE}/customer-row?${stemQuery(stem)}`);
export const fetchTerms = (stem: string) => whenVaultReady(() => apiFetch<CustomerTerms>(`${BASE}/terms?${stemQuery(stem)}`));
export const saveTerms = (stem: string, value: { terms: TermLine[]; note: string }) =>
  apiFetch<CustomerTerms>(`${BASE}/terms?${stemQuery(stem)}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value),
  });
export const fetchReport = (stem: string) => whenVaultReady(() => apiFetch<Report>(`${BASE}/report?${stemQuery(stem)}`));
export const fetchPortfolio = () => whenVaultReady(() => apiFetch<Portfolio>(`${BASE}/portfolio`));
export const fetchSettings = () => apiFetch<InsightSettings>(`${BASE}/settings`);

/** What an import did: written, left as they were (already had terms), and not in this vault. */
export interface TermsImport {
  imported: string[];
  kept: string[];
  missing: string[];
}

/** Every customer's terms as one file, to carry them to another machine. */
export const termsExportPath = () => `${BASE}/terms/export.json`;
export const importTerms = (file: File, replace: boolean) => {
  const form = new FormData();
  form.append('file', file);
  return apiFetch<TermsImport>(`${BASE}/terms/import?replace=${replace}`, { method: 'POST', body: form });
};

/** Paths for an `<a href>`: the browser downloads the workbook itself. */
export const reportExportPath = (stem: string) => `${BASE}/report.xlsx?${stemQuery(stem)}`;
export const portfolioExportPath = () => `${BASE}/portfolio.xlsx`;
