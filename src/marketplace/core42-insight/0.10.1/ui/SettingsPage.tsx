import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { apiUrl } from '../../pluginHost/api';
import { usePluginReturn } from '../../pluginHost/breadcrumbs';
import { useUrlState } from '../../pluginHost/state';
import {
  fetchCustomerList, fetchSettings, fetchTerms, importTerms, saveTerms, termsExportPath,
  type Agreement, type TermsImport, type CustomerTerms, type InsightSettings, type ListedCustomer, type Model, type Payment, type TermLine,
} from './client';
import { PLUGIN_ID, errorText, usd } from './format';

/** How Insight is calculated, chosen as a card (operator, 2026-10-18). */
const MODEL_CARDS: { model: Model; title: string; summary: string }[] = [
  { model: 'percentage', title: 'From monthly %', summary: 'A percentage of what the customer consumes each month, earned when the month ends.' },
  { model: 'upfront', title: 'Up front', summary: 'One fixed fee, billed in the month the line starts.' },
  { model: 'yearly', title: 'Yearly', summary: 'A fixed fee every year, on the anniversary of the line\'s start.' },
];

/** Today in the operator's time zone; toISOString() is UTC and gives yesterday east of Greenwich after midnight. */
function localToday(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
}

const isoDay = (value: string | null | undefined) => (value && /^\d{4}-\d{2}-\d{2}/.test(value) ? value.slice(0, 10) : '');

function dayAfter(day: string): string {
  const next = new Date(`${day}T00:00:00`);
  next.setDate(next.getDate() + 1);
  return `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}-${String(next.getDate()).padStart(2, '0')}`;
}

/** Why a line does not sit within the agreement -- the same rule as the backend's. */
function outsideAgreement(line: TermLine, agreement: Agreement | null): string | null {
  const start = isoDay(agreement?.start);
  const end = isoDay(agreement?.end);
  if (start && line.start && line.start < start) return `Starts before the agreement (${start}).`;
  if (end && line.end && line.end > end) return `Ends after the agreement (${end}).`;
  return null;
}

function AgreementSummary({ agreement }: { agreement: Agreement | null }) {
  if (!agreement) {
    return <p className="insight-agreement text-muted">No agreement on this customer's note or in Azure Customer 360, so dates are not prefilled.</p>;
  }
  return (
    <div className="card insight-agreement">
      <span className="insight-kpi-label">Agreement Insight is attached to</span>
      <strong>
        {agreement.type || 'Agreement'}
        {agreement.amount ? ` · ${usd(agreement.amount)}` : ''}
        {agreement.currency && agreement.currency !== 'USD' ? ` (${agreement.currency})` : ''}
      </strong>
      <span className="text-muted">{isoDay(agreement.start) || '?'} → {isoDay(agreement.end) || '?'}</span>
    </div>
  );
}

/** An up-front fee's instalments; a fee saved before instalments existed reads as one payment on its start. */
function paymentsOf(line: TermLine): Payment[] {
  if (line.payments?.length) return line.payments;
  return [{ date: line.start, amount: line.amount }];
}

function PaymentsEditor({ line, onChange }: { line: TermLine; onChange: (payments: Payment[]) => void }) {
  const payments = paymentsOf(line);
  const update = (index: number, change: Partial<Payment>) =>
    onChange(payments.map((payment, at) => (at === index ? { ...payment, ...change } : payment)));
  const total = payments.reduce((sum, payment) => sum + (payment.amount ?? 0), 0);
  return (
    <div className="insight-payments">
      <span className="insight-kpi-label">Payments of the up-front fee</span>
      {payments.map((payment, index) => (
        <div key={index} className="insight-payment-row">
          <label>Date
            <input type="date" value={payment.date} onChange={(event) => update(index, { date: event.target.value })} />
          </label>
          <label>Amount, USD
            <input type="number" min={0} value={payment.amount ?? ''}
                   onChange={(event) => update(index, { amount: event.target.value === '' ? undefined : Number(event.target.value) })} />
          </label>
          <label className="insight-payment-note">Note
            <input type="text" value={payment.note ?? ''} placeholder="e.g. on signing"
                   onChange={(event) => update(index, { note: event.target.value || undefined })} />
          </label>
          {payments.length > 1 ? (
            <button type="button" className="btn btn-ghost" onClick={() => onChange(payments.filter((_, at) => at !== index))}>Remove</button>
          ) : null}
        </div>
      ))}
      <div className="insight-payment-footer">
        <button type="button" className="btn btn-ghost"
                onClick={() => onChange([...payments, { date: localToday() < line.start ? line.start : localToday() }])}>Add a payment</button>
        <span className="text-muted">Total {usd(total)} in {payments.length} payment{payments.length === 1 ? '' : 's'}</span>
      </div>
    </div>
  );
}

function ModelCards({ value, onChange }: { value: Model; onChange: (model: Model) => void }) {
  return (
    <div className="insight-model-cards" role="radiogroup" aria-label="How Insight is calculated">
      {MODEL_CARDS.map((card) => (
        <button key={card.model} type="button" role="radio" aria-checked={value === card.model} aria-label={card.title}
                className="card insight-model-card" onClick={() => onChange(card.model)}>
          <strong>{card.title}</strong>
          <span>{card.summary}</span>
        </button>
      ))}
    </div>
  );
}

function LineEditor({ line, agreement, onChange, onRemove }: {
  line: TermLine; agreement: Agreement | null; onChange: (line: TermLine) => void; onRemove: () => void;
}) {
  const set = (change: Partial<TermLine>) => onChange({ ...line, ...change });
  const outside = outsideAgreement(line, agreement);
  const agreementStart = isoDay(agreement?.start);
  const agreementEnd = isoDay(agreement?.end);
  const matches = line.start === agreementStart && (line.end ?? '') === agreementEnd;
  return (
    <div className="card insight-line">
      <ModelCards value={line.model} onChange={(model) => set({ model })} />
      <div className="insight-line-fields">
        <label>From
          <input type="date" value={line.start} onChange={(event) => set({ start: event.target.value })} />
        </label>
        <label title="Optional: leave empty while the terms run on">To
          <input type="date" value={line.end ?? ''} onChange={(event) => set({ end: event.target.value || undefined })} />
        </label>
        {line.model === 'percentage' ? (
          <>
            <label>Percent
              <input type="number" min={0} max={100} step={0.01} value={line.percent ?? ''}
                     onChange={(event) => set({ percent: event.target.value === '' ? undefined : Number(event.target.value) })} />
            </label>
            <label className="insight-check">
              <input type="checkbox" checked={line.include_marketplace ?? true}
                     onChange={(event) => set({ include_marketplace: event.target.checked })} /> Include Marketplace
            </label>
            <label className="insight-check">
              <input type="checkbox" checked={line.subtract_credits ?? true}
                     onChange={(event) => set({ subtract_credits: event.target.checked })} /> Subtract credits
            </label>
          </>
        ) : line.model === 'yearly' ? (
          <label>Yearly fee, USD
            <input type="number" min={0} value={line.amount ?? ''}
                   onChange={(event) => set({ amount: event.target.value === '' ? undefined : Number(event.target.value) })} />
          </label>
        ) : null}
        {agreementStart && !matches ? (
          <button type="button" className="btn btn-ghost"
                  onClick={() => set({ start: agreementStart, end: agreementEnd || undefined })}>Match the agreement</button>
        ) : null}
        <button type="button" className="btn btn-ghost insight-line-remove" onClick={onRemove}>Remove</button>
      </div>
      {line.model === 'upfront' ? <PaymentsEditor line={line} onChange={(payments) => set({ payments })} /> : null}
      {outside ? <p className="insight-warn insight-line-warning">{outside}</p> : null}
    </div>
  );
}

function CustomerTermsEditor({ stem, onSaved }: { stem: string; onSaved: () => void }) {
  const [loaded, setLoaded] = useState<CustomerTerms | null>(null);
  const [lines, setLines] = useState<TermLine[]>([]);
  const [note, setNote] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = (terms: CustomerTerms) => {
    setLoaded(terms);
    setLines(terms.terms);
    setNote(terms.note);
    setError(terms.error);
  };

  useEffect(() => {
    setLoaded(null);
    setError(null);
    fetchTerms(stem).then(load, (failure) => setError(errorText(failure)));
  }, [stem]);

  if (!loaded) return error ? <div className="insight-error">{error}</div> : <p className="text-muted">Loading…</p>;

  const following = loaded.inherited_from
    ? `${loaded.inherited_from}'s ${loaded.inherited.map((line) => `${line.percent}%`).join(' then ')} of monthly consumption`
    : null;
  if (!loaded.has_note) {
    return (
      <section className="insight-section">
        <h2>{loaded.name}</h2>
        <p className="card insight-agreement">
          {following ? `Follows ${following}.` : 'Its parent has no percentage, so it is charged nothing.'}
          {' '}It has no Customer note, so it cannot hold Insight terms of its own: create its note in Customers &amp;
          Partners and link it in Azure Customer 360, and it can.
        </p>
      </section>
    );
  }

  // Insight is attached to the agreement (operator, 2026-10-18): the first line
  // runs its whole term, a later one from the day after the previous line ends.
  const addLine = () => {
    const agreement = loaded.agreement;
    const last = lines[lines.length - 1];
    const start = last ? (last.end ? dayAfter(last.end) : localToday()) : (isoDay(agreement?.start) || localToday());
    const end = isoDay(agreement?.end) || undefined;
    setLines([...lines, {
      model: last?.model ?? 'percentage', start, end: end && end >= start ? end : undefined,
      include_marketplace: agreement?.include_marketplace ?? true, subtract_credits: agreement?.subtract_credits ?? true,
    }]);
  };
  const save = () => {
    setSaving(true);
    setError(null);
    const submitted = lines.map((line) => (line.model === 'upfront' ? { ...line, payments: paymentsOf(line) } : line));
    saveTerms(stem, { terms: submitted, note })
      .then((saved) => { load(saved); onSaved(); }, (failure) => setError(errorText(failure)))
      .finally(() => setSaving(false));
  };

  return (
    <section className="insight-section">
      <h2>{loaded.name}</h2>
      <p className="text-muted">
        Choose how Insight is calculated for each period of the agreement. New lines take the agreement's dates.
        One model at a time: end a line before the month the next one starts. A line counts whole months.
        Saved in the vault, in this customer's Insight note.
      </p>
      <AgreementSummary agreement={loaded.agreement} />
      {following && lines.length === 0 ? (
        <p className="text-muted">Follows {following} until you set terms of its own here.</p>
      ) : null}
      {lines.map((line, index) => (
        <LineEditor key={index} line={line} agreement={loaded.agreement}
                    onChange={(changed) => setLines(lines.map((current, at) => (at === index ? changed : current)))}
                    onRemove={() => setLines(lines.filter((_, at) => at !== index))} />
      ))}
      <button type="button" className="btn btn-ghost" onClick={addLine}>
        {lines.length ? 'Add a later period' : 'Set up Insight for this customer'}
      </button>
      <label className="insight-note">Note
        <textarea rows={2} value={note} onChange={(event) => setNote(event.target.value)} />
      </label>
      {error ? <div className="insight-error">{error}</div> : null}
      <div className="insight-actions">
        <button type="button" className="btn btn-primary" disabled={saving} onClick={save}>{saving ? 'Saving…' : 'Save'}</button>
      </div>
    </section>
  );
}

/** Every customer's terms out to a file, or in from one, for a machine without
 *  this vault's Insight notes (operator, 2026-10-23). */
function MoveTerms({ onImported }: { onImported: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [replace, setReplace] = useState(false);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<TermsImport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bringIn = () => {
    if (!file) return;
    setImporting(true); setError(null); setResult(null);
    importTerms(file, replace)
      .then((done) => { setResult(done); setFile(null); onImported(); }, (failure) => setError(errorText(failure)))
      .finally(() => setImporting(false));
  };
  return (
    <section className="insight-section">
      <h2>Move to another machine</h2>
      <p className="text-muted">
        Every customer's Insight terms, as one file. They are kept in the vault, so a machine with the same vault has
        them already; this is for one that does not. Import writes them to the matching Customer notes and skips a
        customer the vault does not have.
      </p>
      <div className="insight-actions">
        <a className="btn" href={apiUrl(termsExportPath())}>Export terms</a>
      </div>
      <div className="insight-actions">
        <input type="file" accept=".json" onChange={(event) => { setFile(event.target.files?.[0] ?? null); setResult(null); }} />
        <label className="insight-check">
          <input type="checkbox" checked={replace} onChange={(event) => setReplace(event.target.checked)} />
          Replace terms a customer already has
        </label>
        <button type="button" className="btn" disabled={!file || importing} onClick={bringIn}>
          {importing ? 'Importing…' : 'Import'}
        </button>
      </div>
      {error ? <div className="insight-error">{error}</div> : null}
      {result ? (
        <p className="text-muted">
          Imported {result.imported.length} customer(s).
          {result.kept.length ? ` Kept the terms ${result.kept.length} already had: ${result.kept.join(', ')}.` : ''}
          {result.missing.length ? ` Not in this vault: ${result.missing.join(', ')}.` : ''}
        </p>
      ) : null}
    </section>
  );
}

export function SettingsPage() {
  const navigate = useNavigate();
  const back = usePluginReturn(PLUGIN_ID);
  const [stem, setStem] = useUrlState('customer');
  const [customers, setCustomers] = useState<ListedCustomer[] | null>(null);
  const [settings, setSettings] = useState<InsightSettings | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = () => fetchCustomerList().then(setCustomers, (failure) => setError(errorText(failure)));
  useEffect(() => {
    reload();
    fetchSettings().then(setSettings, (failure) => setError(errorText(failure)));
  }, []);

  return (
    <div className="insight-settings">
      {settings && !settings.sources.cost_manager ? (
        <div className="insight-error">Azure Customer 360 with the consumption service is needed: Insight reads customers and consumption from it.</div>
      ) : null}
      {settings && !settings.sources.entities ? (
        <div className="insight-error">Entities with Insight terms is needed: Entities keeps the terms in the vault.</div>
      ) : null}
      {error ? <div className="insight-error">{error}</div> : null}
      <section className="insight-section">
        <label>Customer
          <select value={stem} onChange={(event) => setStem(event.target.value)}>
            <option value="">Choose a customer…</option>
            {(customers ?? []).map((customer) => (
              <option key={customer.stem} value={customer.stem}>
                {customer.parent ? '— ' : ''}{customer.name}{customer.has_note ? '' : ' · no note'}
              </option>
            ))}
          </select>
        </label>
      </section>
      {stem ? <CustomerTermsEditor stem={stem} onSaved={() => { reload(); if (back) navigate(back.to); }} /> : null}
      {!stem ? <MoveTerms onImported={reload} /> : null}
    </div>
  );
}
