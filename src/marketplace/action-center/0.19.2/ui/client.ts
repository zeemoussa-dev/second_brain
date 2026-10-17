import { apiFetch } from '../../pluginHost/api';

// The host mounts this plugin's backend under /plugins/<plugin-id>/.
const BASE = '/plugins/action-center';

export interface ActionCenterSummary {
  /** Open actions owed by a team or company, with nobody named yet. */
  not_a_person?: number;
  total: number;
  open: number;
  completed: number;
  dropped: number;
  overdue: number;
  unowned: number;
  unaddressed: number;
  owners: number;
  waiting_on_others: number;
  mine: number;
  by_source: Record<string, number>;
}

export interface ActionItem {
  entity?: string;
  entity_tag?: string;
  /** Whether the vault can say this owner is a person: an address on the
   *  action, or a Person note under that name. */
  owner_is_person?: boolean;
  subject: string;
  owner: string;
  owner_email: string;
  asked_by: string;
  source: string;
  scope: string;
  status: string;
  priority: string;
  due: string | null;
  overdue: boolean;
  asked_at: string | null;
  source_thread: string | null;
  customer: string | null;
  completed_at: string | null;
  evidence: string | null;
  evidence_source: string | null;
  keep_open_until: string | null;
  stem: string;
}

/** Where a linked thread or meeting opens: its Cockpit when it has one, so
 *  the conversation can be picked up there, and always as a plain note. */
export interface LinkedNote {
  stem: string;
  kind: string | null;
  found: boolean;
  cockpit: string | null;
  note: string;
}

export interface ActionDetail extends ActionItem {
  ask: string;
  history: string[];
  chases: string[];
  notes: string[];
  source_link: LinkedNote | null;
  evidence_link: LinkedNote | null;
}

export interface NewAction {
  subject: string;
  owner?: string;
  owner_email?: string;
  due?: string;
  priority?: string;
  scope?: string;
  customer?: string;
  note?: string;
}

export interface ActionGroup {
  key: string;
  count: number;
  overdue: number;
  items: ActionItem[];
}

export interface Facet {
  value: string;
  count: number;
  label?: string;
}

export interface ActionFacets {
  owners: Facet[];
  entities: Facet[];
  customers: Facet[];
  sources: Facet[];
  priorities: Facet[];
  statuses: Facet[];
  scopes: Facet[];
  group_by: string[];
}

export interface ActionFilters {
  status?: string;
  owner?: string;
  customer?: string;
  source?: string;
  priority?: string;
  overdue?: boolean;
  unaddressed?: boolean;
  /** Owned by a team or a company rather than anybody in particular. */
  not_a_person?: boolean;
  /** The company an action is about, from its thread's own tag. */
  entity?: string;
  entity_tag?: string;
  /** Completed on evidence that links to nothing -- the quote is there, what
   *  proves it is not. */
  no_source?: boolean;
  scope?: string;
  q?: string;
}

function query(filters: ActionFilters, extra: Record<string, string> = {}): string {
  const params = new URLSearchParams(extra);
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === '' || value === false) return;
    params.set(key, String(value));
  });
  const text = params.toString();
  return text ? `?${text}` : '';
}

export function fetchActionSummary(): Promise<ActionCenterSummary> {
  return apiFetch<ActionCenterSummary>(`${BASE}/summary`);
}

/** The filter choices for the status being looked at -- the Completed screen
 *  filters over its own actions, not over the open ones. */
export function fetchActionFacets(status = 'Open'): Promise<ActionFacets> {
  return apiFetch<ActionFacets>(`${BASE}/facets?status=${encodeURIComponent(status)}`);
}

export function fetchActions(filters: ActionFilters = {}): Promise<ActionItem[]> {
  return apiFetch<ActionItem[]>(`${BASE}/actions${query(filters)}`);
}

export function fetchActionGroups(groupBy: string, filters: ActionFilters = {}): Promise<ActionGroup[]> {
  return apiFetch<ActionGroup[]>(`${BASE}/grouped${query(filters, { group_by: groupBy })}`);
}

const path = (stem: string) => `${BASE}/actions/${encodeURIComponent(stem)}`;

function send<T>(url: string, method: string, body: unknown): Promise<T> {
  return apiFetch<T>(url, { method, body: JSON.stringify(body) });
}

export function fetchAction(stem: string): Promise<ActionDetail> {
  return apiFetch<ActionDetail>(path(stem));
}

export function createAction(action: NewAction): Promise<{ stem: string }> {
  return send(`${BASE}/actions`, 'POST', action);
}

export function updateAction(stem: string, fields: Partial<NewAction> & { keep_open_until?: string }) {
  return send<{ changed: string[] }>(path(stem), 'PATCH', fields);
}

export function completeAction(stem: string, body: {
  evidence: string; status?: string; evidence_source?: string; condition_met?: boolean;
}) {
  return send(`${path(stem)}/complete`, 'POST', body);
}

export function reopenAction(stem: string, body: { reason: string; keep_open_until?: string }) {
  return send(`${path(stem)}/reopen`, 'POST', body);
}

export function addActionNote(stem: string, text: string) {
  return send(`${path(stem)}/notes`, 'POST', { text });
}

/** What nobody could settle -- the operator's own list. */
export interface DoubtRow {
  stem: string;
  subject: string;
  owner: string;
  customer: string | null;
  due: string | null;
  overdue: boolean;
}

export interface Person {
  /** He addressed this person in the To of his own mail on that thread, which
   *  is the strongest signal of who actually owes it. */
  written_to?: boolean;
  name: string;
  email: string;
}

/** An owner nobody can be messaged about, with the people he sent the ask to. */
export interface UnaddressedOwner {
  owner: string;
  actions: number;
  asks: string[];
  stems: string[];
  candidates: Person[];
}

export type LookalikePair = { owner: string; address: string | null; actions: number }[];

export interface Decision {
  seen: string;
  name: string;
  email: string;
  decided: string;
  by: string;
}

export interface Doubts {
  asked_of_several: { count: number; items: DoubtRow[] };
  no_address: { count: number; owners: number; items: UnaddressedOwner[] };
  possible_duplicate_owners: { count: number; items: LookalikePair[] };
  decided: { count: number; by_the_operator: number; items: Decision[] };
}

export function fetchDoubts(): Promise<Doubts> {
  return apiFetch<Doubts>(`${BASE}/doubts`);
}

/** Name and address every open action of one owner. Recorded as the operator's
 *  decision, which no agent may overwrite. */
export function setOwner(body: {
  owner: string; name?: string; email?: string; clear_address?: boolean;
}): Promise<{ actions_changed: number }> {
  return send(`${BASE}/owners`, 'POST', body);
}

/** Ask the install's own agent to chase this action's owner. The agent writes
 *  the message; it lands in the agent's Drafts, unsent. */
export interface ChaseRules {
  /** While true, a chase may only go to somebody inside the company -- read by
   *  this screen AND by the Skill the cron job runs. */
  internal_only: boolean;
  domains: string[];
}

export function fetchChaseRules(): Promise<ChaseRules> {
  return apiFetch<ChaseRules>(`${BASE}/chase-rules`);
}

export function saveChaseRules(internalOnly: boolean): Promise<ChaseRules> {
  return send(`${BASE}/chase-rules`, 'PUT', { internal_only: internalOnly });
}

export interface ChaseRecipient {
  name: string;
  email: string;
  /** Where the address came from: the owner book, the thread the ask was sent
   *  in, or the action's own field. Empty when nothing could place the name. */
  source: string;
  selected: boolean;
  /** Outside the company, and held back while the internal-only rule stands. */
  external: boolean;
}

/** Who a chase about this action would go to. An ask owed by several people is
 *  one email to all of them, so the screen shows the list before he sends. */
export function fetchChaseRecipients(stem: string): Promise<{
  stem: string; owner: string;
  /** Addresses already settled on this action (`chase_to`), which is what the
   *  ticks come from when it is not empty. */
  settled: string[];
  internal_only: boolean;
  /** Every action this one email covers -- the same ask given to several
   *  people is several actions and one message. */
  stems: string[];
  shared_with: number;
  recipients: ChaseRecipient[];
}> {
  return apiFetch(`${path(stem)}/recipients`);
}

export function chaseOwner(stem: string, to?: string[]): Promise<{
  actions: string[]; agent_started: boolean; note: string;
}> {
  return send(`${path(stem)}/chase`, 'POST', to && to.length ? { to } : {});
}

/** Queue several actions for chasing at once. Still one email per action --
 *  the agent writes each separately; this only saves the pressing. */
export function chaseMany(stems: string[]): Promise<{
  actions: string[]; queued: number; agent_started: boolean; note: string;
  skipped: { stem: string; why: string }[];
}> {
  return send(`${BASE}/chase`, 'POST', { stems });
}
