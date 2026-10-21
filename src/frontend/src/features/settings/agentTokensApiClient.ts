import { apiFetch } from '../../api/client';

// The keys Hermes workers authenticate with (`REQ-SB-103`, `ADR-062`).
//
// One contract this client exists to keep visible to its screen: the
// token text comes back from `mint` and from NOWHERE else. Only its
// SHA-256 is stored, so a list can never show it again and the screen
// has to put it in front of the operator at that one moment.

export interface AgentTokenRow {
  token_sha256: string;
  agent_id: string;
  label: string;
  created_at: string;
  created_by: string;
  last_seen_at: string | null;
  revoked_at: string | null;
  is_revoked: boolean;
  /** A key issued and never used usually means it never reached the
   *  worker — which looks identical to "that agent is quiet" unless the
   *  app says which. */
  has_ever_been_used: boolean;
}

/** The mint response, which is a row PLUS the one and only sight of the
 *  token itself. */
export interface MintedAgentToken extends AgentTokenRow {
  token: string;
  shown_once: string;
}

export function fetchAgentTokens(): Promise<AgentTokenRow[]> {
  return apiFetch('/admin/agent-tokens');
}

export function mintAgentToken(agentId: string, label: string): Promise<MintedAgentToken> {
  return apiFetch('/admin/agent-tokens', {
    method: 'POST',
    body: JSON.stringify({ agent_id: agentId, label }),
  });
}

export function revokeAgentToken(tokenSha256: string): Promise<AgentTokenRow> {
  return apiFetch(`/admin/agent-tokens/${encodeURIComponent(tokenSha256)}`, { method: 'DELETE' });
}
