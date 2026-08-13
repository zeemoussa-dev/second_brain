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

export function approvePendingApproval(approvalId: string): Promise<PendingApproval> {
  return apiFetch<PendingApproval>(`/pending-approvals/${approvalId}/approve`, { method: 'POST' });
}

export function declinePendingApproval(approvalId: string): Promise<PendingApproval> {
  return apiFetch<PendingApproval>(`/pending-approvals/${approvalId}/decline`, { method: 'POST' });
}
