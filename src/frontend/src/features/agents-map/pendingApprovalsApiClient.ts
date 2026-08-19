import { apiFetch } from '../../api/client';

export interface PendingApproval {
  id: string;
  agent_id: string;
  agent_name: string;
  trigger: 'chat' | 'direct' | 'background' | 'hub_routed';
  action_id: string | null;
  description: string;
  status: 'pending' | 'approved' | 'declined';
  created_at: string;
  resolved_at: string | null;
  // Additive (REQ-SB-76-US-01-T08) -- already present on the real API
  // response (pending_approval_registry.py already stores/returns it),
  // simply not yet typed. The Company Review decision control reads
  // payload.thread_paths for its own display; every other proposal kind
  // ignores this field entirely.
  payload?: Record<string, unknown> | null;
}

export interface CompanyReviewDecision {
  outcome: string;
  parent_name?: string;
  parent_kind?: string;
}

export interface KnownCompanies {
  customers: string[];
  partners: string[];
}

export function fetchPendingApprovals(params?: {
  status?: string;
  agent_id?: string;
}): Promise<PendingApproval[]> {
  const query = new URLSearchParams();
  if (params?.status) query.set('status', params.status);
  if (params?.agent_id) query.set('agent_id', params.agent_id);
  const qs = query.toString();
  return apiFetch<PendingApproval[]>(`/pending-approvals${qs ? `?${qs}` : ''}`);
}

export function fetchPendingApproval(approvalId: string): Promise<PendingApproval> {
  return apiFetch<PendingApproval>(`/pending-approvals/${approvalId}`);
}

export function approvePendingApproval(
  approvalId: string,
  decision?: CompanyReviewDecision,
): Promise<PendingApproval> {
  return apiFetch<PendingApproval>(`/pending-approvals/${approvalId}/approve`, {
    method: 'POST',
    ...(decision ? { body: JSON.stringify(decision) } : {}),
  });
}

export function declinePendingApproval(approvalId: string): Promise<PendingApproval> {
  return apiFetch<PendingApproval>(`/pending-approvals/${approvalId}/decline`, { method: 'POST' });
}

export function fetchKnownCompanies(): Promise<KnownCompanies> {
  return apiFetch<KnownCompanies>('/pending-approvals/known-companies');
}
