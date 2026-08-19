import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import {
  fetchPendingApprovals,
  fetchKnownCompanies,
  approvePendingApproval,
  declinePendingApproval,
  type PendingApproval,
  type CompanyReviewDecision,
  type KnownCompanies,
} from '../features/agents-map/pendingApprovalsApiClient';

const COMPANY_REVIEW_ACTION_ID = 'propose_company_review';

export function MyDayApprovalsPage() {
  const [items, setItems] = useState<PendingApproval[] | null>(null);
  const [knownCompanies, setKnownCompanies] = useState<KnownCompanies | null>(null);

  function refresh() {
    fetchPendingApprovals({ status: 'pending' }).then(setItems);
  }

  useEffect(() => {
    refresh();
    // Fresh on every page load (REQ-SB-76-US-01-T08) -- never baked into a
    // proposal's own stored payload, which would go stale the moment ANY
    // other Company Review batch resolves first.
    fetchKnownCompanies().then(setKnownCompanies);
  }, []);

  async function handleApprove(id: string) {
    await approvePendingApproval(id);
    refresh();
  }

  async function handleDecline(id: string) {
    await declinePendingApproval(id);
    refresh();
  }

  async function handleCompanyReviewDecision(id: string, decision: CompanyReviewDecision) {
    await approvePendingApproval(id, decision);
    refresh();
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
      <h1>Pending Approvals</h1>
      <p className="text-muted">
        Actions a Supervised agent has proposed on its own background/
        scheduled pipeline trigger and is waiting on your approval before
        taking. Chat-triggered proposals from an active conversation
        appear inline in that agent's own Chat panel on the Agents Map
        instead of here. Change an agent's working mode from its Agent
        Settings panel.
      </p>
      <div className="card">
        {items && items.length > 0 ? (
          <div className="item-list">
            {items.map((item) => (
              <div className="item-row" key={item.id}>
                <div className="item-row-main">
                  <span className="item-row-title">
                    {item.agent_name} <span className="badge badge-warning">Awaiting approval</span>
                  </span>
                  <span className="item-row-meta">{item.description}</span>
                </div>
                {item.action_id === COMPANY_REVIEW_ACTION_ID ? (
                  <CompanyReviewDecisionControl
                    item={item}
                    knownCompanies={knownCompanies}
                    onDecide={handleCompanyReviewDecision}
                    onDecline={handleDecline}
                  />
                ) : (
                  <div className="item-row-actions">
                    <button type="button" className="btn btn-primary" onClick={() => handleApprove(item.id)}>
                      Approve
                    </button>
                    <button type="button" className="btn btn-danger" onClick={() => handleDecline(item.id)}>
                      Decline
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          items && (
            <div className="empty-state">
              <div className="empty-state-icon">&#10003;</div>
              <p><strong>Nothing awaiting approval right now.</strong></p>
              <p className="text-muted">
                Every Supervised agent's queue is caught up. Proposals from
                a background/scheduled pipeline trigger will appear here
                as soon as one is raised.
              </p>
            </div>
          )
        )}
      </div>
    </>
  );
}

// The Company Review proposal kind's own distinct 5-way decision control
// (REQ-SB-76-US-01-T08, ADR-057 Decision 3/7) -- Customer/Partner resolve
// in one click; Affiliate reveals a parent picker (sourced from
// knownCompanies) plus a Customer-or-Partner kind choice for the NEW
// entity itself; Merge reveals a parent picker only -- the picked option's
// own list membership (customers vs. partners) resolves parent_kind, so
// the operator is never asked to choose it separately for Merge. Built
// directly using this app's own existing form/control vocabulary (`btn`/
// `btn-primary`/`btn-danger`, `input` for select) -- no `/design` pass, per
// the story's own operator override.
function CompanyReviewDecisionControl({
  item,
  knownCompanies,
  onDecide,
  onDecline,
}: {
  item: PendingApproval;
  knownCompanies: KnownCompanies | null;
  onDecide: (id: string, decision: CompanyReviewDecision) => void;
  onDecline: (id: string) => void;
}) {
  const [step, setStep] = useState<'choose' | 'affiliate' | 'merge'>('choose');
  const [parentName, setParentName] = useState('');
  const [affiliateKind, setAffiliateKind] = useState<'customer' | 'partner'>('customer');

  const parentOptions = [
    ...(knownCompanies?.customers ?? []).map((name) => ({ name, kind: 'customer' as const })),
    ...(knownCompanies?.partners ?? []).map((name) => ({ name, kind: 'partner' as const })),
  ];

  function resetPicker() {
    setStep('choose');
    setParentName('');
    setAffiliateKind('customer');
  }

  function submitAffiliate() {
    if (!parentName) return;
    onDecide(item.id, { outcome: 'affiliate', parent_name: parentName, parent_kind: affiliateKind });
    resetPicker();
  }

  function submitMerge() {
    const picked = parentOptions.find((option) => option.name === parentName);
    if (!picked) return;
    onDecide(item.id, { outcome: 'merge', parent_name: picked.name, parent_kind: picked.kind });
    resetPicker();
  }

  if (step === 'affiliate') {
    return (
      <div className="item-row-actions" data-testid="company-review-affiliate-picker">
        <select
          className="input"
          value={parentName}
          onChange={(event) => setParentName(event.target.value)}
        >
          <option value="">Choose a parent…</option>
          {parentOptions.map((option) => (
            <option key={`${option.kind}:${option.name}`} value={option.name}>{option.name}</option>
          ))}
        </select>
        <select
          className="input"
          value={affiliateKind}
          onChange={(event) => setAffiliateKind(event.target.value as 'customer' | 'partner')}
        >
          <option value="customer">File new entity as Customer</option>
          <option value="partner">File new entity as Partner</option>
        </select>
        <button type="button" className="btn btn-primary" disabled={!parentName} onClick={submitAffiliate}>
          Confirm Affiliate
        </button>
        <button type="button" className="btn" onClick={resetPicker}>Back</button>
      </div>
    );
  }

  if (step === 'merge') {
    return (
      <div className="item-row-actions" data-testid="company-review-merge-picker">
        <select
          className="input"
          value={parentName}
          onChange={(event) => setParentName(event.target.value)}
        >
          <option value="">Choose the canonical entity…</option>
          {parentOptions.map((option) => (
            <option key={`${option.kind}:${option.name}`} value={option.name}>{option.name}</option>
          ))}
        </select>
        <button type="button" className="btn btn-primary" disabled={!parentName} onClick={submitMerge}>
          Confirm Merge
        </button>
        <button type="button" className="btn" onClick={resetPicker}>Back</button>
      </div>
    );
  }

  return (
    <div className="item-row-actions" data-testid="company-review-decision">
      <button type="button" className="btn btn-primary" onClick={() => onDecide(item.id, { outcome: 'customer' })}>
        Customer
      </button>
      <button type="button" className="btn btn-primary" onClick={() => onDecide(item.id, { outcome: 'partner' })}>
        Partner
      </button>
      <button type="button" className="btn" onClick={() => setStep('affiliate')}>Affiliate</button>
      <button type="button" className="btn" onClick={() => setStep('merge')}>Merge</button>
      <button type="button" className="btn btn-danger" onClick={() => onDecline(item.id)}>Decline</button>
    </div>
  );
}
