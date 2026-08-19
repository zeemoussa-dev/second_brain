// Pending Approvals grouping/color lookup (REQ-SB-78-US-01-T01) -- a new,
// small, static, frontend-only table mapping action_id -> {label,
// colorClass}, per architecture.md's own "Pending Approvals — Grouped,
// Color-Coded Review" § "Label + color". Every action_id NOT in
// KNOWN_GROUPS (including a null background-trigger action_id, and every
// migrated mutating Skill id) falls into the ONE OTHER_GROUP catch-all --
// forward-compatible by construction, no code change needed here to stay
// visibly, honestly grouped when a future story adds a new action_id.

export const KNOWN_GROUPS: Record<string, { label: string; colorClass: string }> = {
  propose_company_review:              { label: 'Company Review',         colorClass: 'group-color-1' },
  propose_customer_backfill_routing:   { label: 'Customer Backfill',      colorClass: 'group-color-2' },
  propose_customer_archival_candidate: { label: 'Customer Archival',      colorClass: 'group-color-3' },
  propose_librarian_company_link:      { label: 'Company Link',           colorClass: 'group-color-4' },
  route_thread_to_project:             { label: 'Thread Routing',         colorClass: 'group-color-5' },
  propose_recurring_pipeline:          { label: 'Recurring Pipeline',     colorClass: 'group-color-6' },
  propose_cross_cutting_update:        { label: 'Cross-Cutting Update',   colorClass: 'group-color-7' },
  propose_background_amendment:        { label: 'Background Amendment',   colorClass: 'group-color-8' },
  propose_new_top_level_area:          { label: 'New Top-Level Area',     colorClass: 'group-color-9' },
  hermes_vault_write:                  { label: 'Hermes Write',           colorClass: 'group-color-10' },
  acknowledge_classification_failure:  { label: 'Classification Failure', colorClass: 'group-color-11' },
};

export const OTHER_GROUP = { label: 'Other', colorClass: 'group-color-other' };

// Groups whose items carry a genuine branching decision (no single
// unambiguous "approve" to bulk-apply) -- reused/generalized by T03 to
// gate the bulk-approve control per rendered group. Today: exactly the
// Company Review 5-way control's own action_id.
export const BRANCHING_DECISION_ACTION_IDS = new Set(['propose_company_review']);

export function resolveGroup(actionId: string | null): { key: string; label: string; colorClass: string } {
  if (actionId && actionId in KNOWN_GROUPS) {
    return { key: actionId, ...KNOWN_GROUPS[actionId] };
  }
  return { key: 'other', ...OTHER_GROUP };
}
