// The frontend half of the Plugin API (ADR-022): the only framework module a
// plugin's screens may import, apart from the contract in ./types. A screen
// that imports anything else from the framework -- a feature, a page, the
// API client directly -- breaks the next time that module changes, even
// though its framework_api still matches.

import { fetchPendingApprovals } from '../features/agents-map/pendingApprovalsApiClient';

export { apiFetch, ApiError } from '../api/client';

/** How many agent proposals are waiting on the operator. The approvals
 * themselves are a framework screen at `/approvals`; a plugin may show the
 * count and link there, never act on an approval itself. */
export function fetchPendingApprovalCount(): Promise<number> {
  return fetchPendingApprovals({ status: 'pending' }).then((items) => items.length);
}
