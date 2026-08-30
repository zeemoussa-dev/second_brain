import { useEffect, useState } from 'react';
import {
  fetchAgent,
  fetchAgentHistory,
  fetchAgentKnowledgeGaps,
  fetchAgentList,
  researchKnowledgeGap,
  resolveKnowledgeGap,
  updateAgentAssignment,
  type AgentDetail,
  type AgentHistoryEntry,
  type AgentSummary,
  type KnowledgeGapsResponse,
} from './agentsApiClient';
import { fetchSections, type SectionSummary } from '../settings/settingsApiClient';
import { FieldEditorModal } from './FieldEditorModal';
import { ExpandableText } from './ExpandableText';
import { ChecklistPicker, type ChecklistItem } from './ChecklistPicker';
import { TagTreePicker } from './TagTreePicker';
import { fetchToolCatalog } from './toolsApiClient';
import { fetchIndexes, type IndexSummary } from './indexesApiClient';
import {
  fetchPendingApproval,
  approvePendingApproval,
  declinePendingApproval,
  type PendingApproval,
} from './pendingApprovalsApiClient';
import { fetchSkills, fetchAgentSkills, grantAgentSkill, revokeAgentSkill, type SkillSummary } from './skillsApiClient';
import { SkillsTree, type SkillsTreeSkill } from './SkillsTree';
import { VisualPicker } from './VisualPicker';
import { fetchScopeSuggestions, type ScopeSuggestions } from '../vault-browser/client';
import {
  fetchSchedules,
  createSchedule,
  updateSchedule,
  removeSchedule,
  runScheduleNow,
  type AgentSchedule,
} from './agentSchedulesApiClient';
import { ApiError } from '../../api/client';
import { AgentChatPanel } from '../chat/AgentChatPanel';
import { fetchHermesSessions, type HermesSession } from '../hermes-ops/client';

interface AgentDetailPanelProps {
  agentId: string;
  onClose: () => void;
  // 2026-08-22 -- this panel's own `agent` state updates immediately on a
  // successful mutation (setAgent(updated) below), so the panel itself
  // always looked right; but AgentsMapPage's own separate `agents`/
  // `fullAgents` state (what the actual map canvas renders from) never
  // got told anything changed, so the NODE on the map stayed stale until
  // a full page reload re-ran refreshAgents(). Optional so this panel
  // still works standalone/in tests with no parent to notify.
  onAgentUpdated?: () => void;
}

const TABS = ['overview', 'chat', 'history', 'settings', 'schedule', 'visual'] as const;
type Tab = (typeof TABS)[number] | 'gaps';
const TAB_LABELS: Record<Tab, string> = {
  overview: 'Overview',
  chat: 'Chat',
  history: 'History',
  settings: 'Settings',
  schedule: 'Schedule',
  visual: 'Visual',
  gaps: 'Knowledge gaps',
};

const INTERVAL_UNITS = ['minutes', 'hours'] as const;

function getAgentPurpose(agent: AgentDetail): string {
  const purposeEntry = agent.settings.find((row) => row.key === 'Purpose');
  if (purposeEntry) return purposeEntry.value;
  const domainEntry = agent.settings.find((row) => row.key === 'Domain');
  if (domainEntry) return domainEntry.value;
  // 2026-08-22 -- a Hermes-sourced agent (ADR-003/004) never has a
  // Purpose/Domain settings row (that shape is deliberately never
  // fabricated), but DOES have a real `prompt` (its own profile's real
  // description/SOUL.md excerpt) -- fall back to that before giving up.
  if (agent.prompt) return agent.prompt;
  return 'No stated purpose recorded for this agent.';
}

const WORKING_MODE_LABELS: Record<AgentDetail['working_mode'], string> = {
  autonomous: 'Autonomous',
  supervised: 'Supervised',
  manual: 'Manual',
};

// Same formatting as AgentActivityPage.tsx's own (duplicated per this
// codebase's small-helper convention, ADR-002) -- Hermes session
// timestamps are real UNIX epoch seconds, not pre-formatted strings.
function formatSessionTimestamp(epochSeconds: number | null): string {
  if (epochSeconds === null) return '—';
  return new Date(epochSeconds * 1000).toLocaleString();
}

function formatSessionDuration(startedAt: number | null, endedAt: number | null): string {
  if (startedAt === null || endedAt === null) return '—';
  const totalSeconds = Math.max(0, Math.round(endedAt - startedAt));
  if (totalSeconds < 60) return `${totalSeconds}s`;
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

// The full catalog (all 11 real Skills, REQ-SB-48-US-01-AC-01), each marked
// granted/not-yet-granted against the agent's own current skill-kind
// capabilities -- SkillsTree groups this combined list by "tool" itself.
function buildSkillsTreeItems(catalog: SkillSummary[], capabilities: AgentDetail['capabilities']): SkillsTreeSkill[] {
  const grantedIds = new Set(capabilities.filter((capability) => capability.kind === 'skill').map((capability) => capability.id));
  return catalog.map((skill) => ({
    id: skill.id,
    name: skill.name,
    tool: skill.tool,
    granted: grantedIds.has(skill.id),
  }));
}

export function AgentDetailPanel({ agentId, onClose, onAgentUpdated }: AgentDetailPanelProps) {
  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [history, setHistory] = useState<AgentHistoryEntry[] | null>(null);
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  const [skillCatalog, setSkillCatalog] = useState<SkillSummary[] | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [scopeDraft, setScopeDraft] = useState('');
  const [toolsDraft, setToolsDraft] = useState('');
  const [dependsOnDraft, setDependsOnDraft] = useState('');
  const [preferredIndexIdsDraft, setPreferredIndexIdsDraft] = useState('');
  const [promptDraft, setPromptDraft] = useState('');
  const [guardrailsDraft, setGuardrailsDraft] = useState('');
  const [scopeSuggestions, setScopeSuggestions] = useState<ScopeSuggestions | null>(null);
  const [approvals, setApprovals] = useState<Record<string, PendingApproval>>({});
  const [gapsData, setGapsData] = useState<KnowledgeGapsResponse | null>(null);
  // 2026-08-23 -- this Agent's own real Hermes session log (operator:
  // "the Overview tab should show these Hermes sessions per agent too"),
  // server-side filtered by agentId (a real Agent's own id IS its real
  // Hermes profile id -- hermes_definitions.py's own PRIMARY_PROFILE_ID =
  // "default" etc.). null while not yet fetched, [] once fetched with no
  // real sessions found (a Pipeline id, or a genuinely brand-new Agent) --
  // never fabricated as a placeholder entry either way.
  const [hermesSessions, setHermesSessions] = useState<HermesSession[] | null>(null);
  const [gapAnswerDrafts, setGapAnswerDrafts] = useState<Record<string, string>>({});
  const [researchingGapId, setResearchingGapId] = useState<string | null>(null);
  const [schedules, setSchedules] = useState<AgentSchedule[] | null>(null);
  const [agentSkills, setAgentSkills] = useState<SkillSummary[] | null>(null);
  const [scheduleEditingCapabilityId, setScheduleEditingCapabilityId] = useState<string | null>(null);
  const [scheduleCapabilityDraft, setScheduleCapabilityDraft] = useState('');
  const [scheduleIntervalValueDraft, setScheduleIntervalValueDraft] = useState('60');
  const [scheduleIntervalUnitDraft, setScheduleIntervalUnitDraft] = useState<(typeof INTERVAL_UNITS)[number]>('minutes');
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [scheduleSaving, setScheduleSaving] = useState(false);
  const [runningNowCapabilityId, setRunningNowCapabilityId] = useState<string | null>(null);
  // 2026-08-29 UI bug list, item 2 -- "Capabilities" starts collapsed;
  // clicking its header reveals the built-in list + SkillsTree beneath it.
  const [capabilitiesExpanded, setCapabilitiesExpanded] = useState(false);
  // 2026-08-29 UI bug list, item 4 -- the suggestions dropdown used to key
  // off scopeDraft alone, so a committed value that happened to also be a
  // real tag (e.g. "customer/adnoc") matched itself and stayed rendered,
  // permanently overlapping the row beneath it. Gate it on real focus too.
  const [scopeInputFocused, setScopeInputFocused] = useState(false);
  // 2026-08-29 (operator: "we need a Big Pop up so we can fill the
  // fields that needs a space to fill") -- which field's big-popup
  // editor is currently open, if any. Each opens its own array-shaped
  // draft below (initialized from the real agent field on open), kept
  // separate from the existing comma-string row drafts above so the
  // inline row editors are untouched by this.
  const [openFieldEditor, setOpenFieldEditor] = useState<
    null | 'prompt' | 'guardrails' | 'scope' | 'tools' | 'dependsOn' | 'preferredIndexes'
  >(null);
  const [savingFieldEditor, setSavingFieldEditor] = useState(false);
  const [scopeEditorDraft, setScopeEditorDraft] = useState<string[]>([]);
  const [toolsEditorDraft, setToolsEditorDraft] = useState<string[]>([]);
  const [dependsOnEditorDraft, setDependsOnEditorDraft] = useState<string[]>([]);
  const [preferredIndexIdsEditorDraft, setPreferredIndexIdsEditorDraft] = useState<string[]>([]);
  // Catalogs for the pickers above -- fetched lazily the first time their
  // own editor opens (each is a real, shared, agent-independent list;
  // no reason to fetch it for every agent detail load if the popup is
  // never opened), then kept for the rest of this panel's lifetime.
  const [toolCatalog, setToolCatalog] = useState<string[] | null>(null);
  const [agentCatalog, setAgentCatalog] = useState<AgentSummary[] | null>(null);
  const [indexCatalog, setIndexCatalog] = useState<IndexSummary[] | null>(null);

  useEffect(() => {
    setAgent(null); // clear stale content immediately on agent switch
    setHistory(null); // clear the previous agent's history on switch
    setActiveTab('overview');
    setScopeDraft('');
    setToolsDraft('');
    setDependsOnDraft('');
    setPreferredIndexIdsDraft('');
    setPromptDraft('');
    setGuardrailsDraft('');
    setScopeSuggestions(null); // clear the previous agent's suggestion snapshot on switch
    setGapsData(null);
    setHermesSessions(null); // clear the previous agent's session log on switch
    setGapAnswerDrafts({});
    setResearchingGapId(null);
    setSchedules(null); // clear the previous agent's schedules on switch
    setAgentSkills(null);
    setScheduleEditingCapabilityId(null);
    setScheduleCapabilityDraft('');
    setScheduleIntervalValueDraft('60');
    setScheduleIntervalUnitDraft('minutes');
    setScheduleError(null);
    fetchAgent(agentId).then((detail) => {
      setAgent(detail);
      setScopeDraft(detail.scope.join(', '));
      setToolsDraft(detail.tools.join(', '));
      setDependsOnDraft(detail.depends_on.join(', '));
      setPreferredIndexIdsDraft(detail.preferred_index_ids.join(', '));
      setPromptDraft(detail.prompt ?? '');
      setGuardrailsDraft(detail.guardrails);
    });
    fetchAgentHistory(agentId).then(setHistory);
    fetchSections().then(setSections);
    fetchSkills().then(setSkillCatalog);
    fetchScopeSuggestions().then(setScopeSuggestions);
  }, [agentId]);

  useEffect(() => {
    if (!history) return;
    for (const entry of history) {
      if (entry.kind === 'proposal' && entry.pending_approval_id) {
        const id = entry.pending_approval_id;
        // A stale/unresolvable pending_approval_id (e.g. leftover smoke-
        // check history debris) must not surface as an unhandled promise
        // rejection -- the card simply stays in its default pending
        // styling rather than crashing the panel.
        fetchPendingApproval(id)
          .then((approval) => {
            setApprovals((prev) => ({ ...prev, [id]: approval }));
          })
          .catch(() => {});
      }
    }
  }, [history]);

  useEffect(() => {
    if (activeTab === 'gaps' && agent?.type === 'expert') {
      fetchAgentKnowledgeGaps(agentId).then(setGapsData);
    }
  }, [activeTab, agentId, agent?.type]);

  useEffect(() => {
    if (activeTab === 'overview' && agent?.type === 'expert') {
      fetchAgentKnowledgeGaps(agentId).then(setGapsData);
    }
  }, [activeTab, agentId, agent?.type]);

  useEffect(() => {
    // History tab, not Overview (operator, 2026-08-23: "The Hermes
    // Sessions in Agent Should be in the History not in Overview").
    if (activeTab !== 'history') return;
    fetchHermesSessions(30, 0, agentId).then((response) => setHermesSessions(response.sessions));
  }, [activeTab, agentId]);

  function refetchSchedulesAndHistory() {
    fetchSchedules(agentId).then(setSchedules);
    fetchAgentHistory(agentId).then(setHistory);
  }

  useEffect(() => {
    if (activeTab !== 'schedule') return;
    fetchSchedules(agentId).then(setSchedules);
    fetchAgentSkills(agentId).then(setAgentSkills);
  }, [activeTab, agentId]);

  async function handleSectionChange(sectionId: string) {
    const updated = await updateAgentAssignment(agentId, { section_id: sectionId });
    setAgent(updated);
    onAgentUpdated?.();
  }

  async function handleIsBackgroundAgentChange(isBackgroundAgent: boolean) {
    const updated = await updateAgentAssignment(agentId, { is_background_agent: isBackgroundAgent });
    setAgent(updated);
    onAgentUpdated?.();
  }

  async function handleIconChange(iconId: string) {
    const updated = await updateAgentAssignment(agentId, { icon: iconId });
    setAgent(updated);
    onAgentUpdated?.();
  }

  async function handleColorChange(colorHex: string) {
    const updated = await updateAgentAssignment(agentId, { color: colorHex });
    setAgent(updated);
    onAgentUpdated?.();
  }

  async function handleVisualReset() {
    // "" is the backend's own clear-to-default sentinel
    // (agent_visual_registry.py) — distinct from omitting the field.
    const updated = await updateAgentAssignment(agentId, { icon: '', color: '' });
    setAgent(updated);
    onAgentUpdated?.();
  }

  async function handleApprove(approvalId: string) {
    const updated = await approvePendingApproval(approvalId);
    setApprovals((prev) => ({ ...prev, [approvalId]: updated }));
    fetchAgentHistory(agentId).then(setHistory);
  }

  async function handleDecline(approvalId: string) {
    const updated = await declinePendingApproval(approvalId);
    setApprovals((prev) => ({ ...prev, [approvalId]: updated }));
    fetchAgentHistory(agentId).then(setHistory);
  }

  async function handleGrantSkill(skillId: string) {
    await grantAgentSkill(agentId, skillId);
    const updated = await fetchAgent(agentId);
    setAgent(updated);
    onAgentUpdated?.();
  }

  // Multi-select bulk actions (REQ-SB-48-US-01-T02) -- N sequential calls to
  // the same single-Skill grantAgentSkill/revokeAgentSkill primitive
  // handleGrantSkill above already uses, never a new batch endpoint; one
  // combined refetch after the whole batch rather than one per Skill. Bulk
  // revoke is now the only revoke path (2026-08-29 UI bug list, item 3
  // removed the per-row Revoke button in favor of Grant-disables-in-place +
  // this checkbox/bulk-action mechanism).
  async function handleBulkGrantSkills(skillIds: string[]) {
    for (const skillId of skillIds) {
      await grantAgentSkill(agentId, skillId);
    }
    const updated = await fetchAgent(agentId);
    setAgent(updated);
    onAgentUpdated?.();
  }

  async function handleBulkRevokeSkills(skillIds: string[]) {
    for (const skillId of skillIds) {
      await revokeAgentSkill(agentId, skillId);
    }
    const updated = await fetchAgent(agentId);
    setAgent(updated);
    onAgentUpdated?.();
  }

  async function handleToolsCommit() {
    const tools = toolsDraft
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    const updated = await updateAgentAssignment(agentId, { tools });
    setAgent(updated);
    onAgentUpdated?.();
    setToolsDraft(updated.tools.join(', '));
  }

  async function handleDependsOnCommit() {
    const dependsOn = dependsOnDraft
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    const updated = await updateAgentAssignment(agentId, { depends_on: dependsOn });
    setAgent(updated);
    onAgentUpdated?.();
    setDependsOnDraft(updated.depends_on.join(', '));
  }

  async function handlePreferredIndexIdsCommit() {
    const preferredIndexIds = preferredIndexIdsDraft
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    const updated = await updateAgentAssignment(agentId, { preferred_index_ids: preferredIndexIds });
    setAgent(updated);
    onAgentUpdated?.();
    setPreferredIndexIdsDraft(updated.preferred_index_ids.join(', '));
  }

  async function handleScopeCommit() {
    const scope = scopeDraft
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    const updated = await updateAgentAssignment(agentId, { scope });
    setAgent(updated);
    onAgentUpdated?.();
    setScopeDraft(updated.scope.join(', '));
  }

  async function handlePromptCommit() {
    const updated = await updateAgentAssignment(agentId, { prompt: promptDraft });
    setAgent(updated);
    onAgentUpdated?.();
    setPromptDraft(updated.prompt ?? '');
  }

  async function handleGuardrailsCommit() {
    const updated = await updateAgentAssignment(agentId, { guardrails: guardrailsDraft });
    setAgent(updated);
    onAgentUpdated?.();
    setGuardrailsDraft(updated.guardrails);
  }

  function openScopeEditor() {
    setScopeEditorDraft(agent?.scope ?? []);
    setOpenFieldEditor('scope');
  }

  function openToolsEditor() {
    setToolsEditorDraft(agent?.tools ?? []);
    setOpenFieldEditor('tools');
    if (!toolCatalog) fetchToolCatalog().then(setToolCatalog);
  }

  function openDependsOnEditor() {
    setDependsOnEditorDraft(agent?.depends_on ?? []);
    setOpenFieldEditor('dependsOn');
    if (!agentCatalog) fetchAgentList().then(setAgentCatalog);
  }

  function openPreferredIndexesEditor() {
    setPreferredIndexIdsEditorDraft(agent?.preferred_index_ids ?? []);
    setOpenFieldEditor('preferredIndexes');
    if (!indexCatalog) fetchIndexes().then(setIndexCatalog);
  }

  function toggleInDraft(setter: (updater: (prev: string[]) => string[]) => void, id: string) {
    setter((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function handleSaveFieldEditor() {
    if (!openFieldEditor) return;
    setSavingFieldEditor(true);
    try {
      if (openFieldEditor === 'prompt') {
        await handlePromptCommit();
      } else if (openFieldEditor === 'guardrails') {
        await handleGuardrailsCommit();
      } else if (openFieldEditor === 'scope') {
        const updated = await updateAgentAssignment(agentId, { scope: scopeEditorDraft });
        setAgent(updated);
        onAgentUpdated?.();
        setScopeDraft(updated.scope.join(', '));
      } else if (openFieldEditor === 'tools') {
        const updated = await updateAgentAssignment(agentId, { tools: toolsEditorDraft });
        setAgent(updated);
        onAgentUpdated?.();
        setToolsDraft(updated.tools.join(', '));
      } else if (openFieldEditor === 'dependsOn') {
        const updated = await updateAgentAssignment(agentId, { depends_on: dependsOnEditorDraft });
        setAgent(updated);
        onAgentUpdated?.();
        setDependsOnDraft(updated.depends_on.join(', '));
      } else if (openFieldEditor === 'preferredIndexes') {
        const updated = await updateAgentAssignment(agentId, { preferred_index_ids: preferredIndexIdsEditorDraft });
        setAgent(updated);
        onAgentUpdated?.();
        setPreferredIndexIdsDraft(updated.preferred_index_ids.join(', '));
      }
      setOpenFieldEditor(null);
    } finally {
      setSavingFieldEditor(false);
    }
  }

  // REQ-SB-50-US-01-T02 -- the last, uncommitted comma-separated token is
  // what a suggestion click replaces; every earlier, already-committed
  // token is left untouched.
  function getInProgressScopeToken(): string {
    const parts = scopeDraft.split(',');
    return (parts[parts.length - 1] ?? '').trim();
  }

  function getFilteredScopeSuggestions(): string[] {
    const token = getInProgressScopeToken().toLowerCase();
    if (!token || !scopeSuggestions) return [];
    const candidates = [...scopeSuggestions.tags.map((entry) => entry.tag), ...scopeSuggestions.folders];
    return candidates.filter((value) => value.toLowerCase().includes(token));
  }

  // A second, additional commit path alongside handleScopeCommit's own
  // typed+blur commit -- does not replace it. Drops the in-progress token
  // and appends the selected suggestion in its place, deduped, leaving
  // every already-committed value untouched/unreordered.
  async function handleScopeSuggestionSelect(value: string) {
    const parts = scopeDraft.split(',').map((entry) => entry.trim());
    parts.pop();
    const nextScope = Array.from(new Set([...parts.filter((entry) => entry.length > 0), value]));
    const updated = await updateAgentAssignment(agentId, { scope: nextScope });
    setAgent(updated);
    onAgentUpdated?.();
    setScopeDraft(updated.scope.join(', '));
  }

  function getSchedulableCapabilities(): SkillSummary[] {
    return (agentSkills ?? []).filter((skill) => skill.mutates);
  }

  function startEditSchedule(schedule: AgentSchedule) {
    setScheduleEditingCapabilityId(schedule.capability_id);
    setScheduleCapabilityDraft(schedule.capability_id);
    setScheduleIntervalValueDraft(String(schedule.interval_value));
    setScheduleIntervalUnitDraft(schedule.interval_unit);
    setScheduleError(null);
  }

  function resetScheduleForm() {
    setScheduleEditingCapabilityId(null);
    setScheduleCapabilityDraft('');
    setScheduleIntervalValueDraft('60');
    setScheduleIntervalUnitDraft('minutes');
    setScheduleError(null);
  }

  async function handleScheduleSave() {
    const capabilityId = scheduleCapabilityDraft;
    const intervalValue = Number.parseInt(scheduleIntervalValueDraft, 10);
    if (!capabilityId || Number.isNaN(intervalValue) || intervalValue <= 0) return;
    setScheduleSaving(true);
    setScheduleError(null);
    try {
      if (scheduleEditingCapabilityId) {
        await updateSchedule(agentId, scheduleEditingCapabilityId, {
          interval_value: intervalValue,
          interval_unit: scheduleIntervalUnitDraft,
          new_capability_id: capabilityId !== scheduleEditingCapabilityId ? capabilityId : undefined,
        });
      } else {
        await createSchedule(agentId, {
          capability_id: capabilityId,
          interval_value: intervalValue,
          interval_unit: scheduleIntervalUnitDraft,
        });
      }
      resetScheduleForm();
      fetchSchedules(agentId).then(setSchedules);
    } catch (error) {
      setScheduleError(error instanceof ApiError ? error.message : 'Could not save this schedule.');
    } finally {
      setScheduleSaving(false);
    }
  }

  async function handleScheduleRemove(capabilityId: string) {
    await removeSchedule(agentId, capabilityId);
    if (scheduleEditingCapabilityId === capabilityId) resetScheduleForm();
    fetchSchedules(agentId).then(setSchedules);
  }

  async function handleRunScheduleNow(capabilityId: string) {
    setRunningNowCapabilityId(capabilityId);
    try {
      await runScheduleNow(agentId, capabilityId);
    } finally {
      setRunningNowCapabilityId(null);
      refetchSchedulesAndHistory();
    }
  }

  async function handleResolveGap(gapId: string) {
    const answer = (gapAnswerDrafts[gapId] ?? '').trim();
    if (!answer) return;
    await resolveKnowledgeGap(agentId, gapId, answer);
    setGapAnswerDrafts((prev) => ({ ...prev, [gapId]: '' }));
    fetchAgentKnowledgeGaps(agentId).then(setGapsData);
  }

  async function handleResearchGap(gapId: string) {
    setResearchingGapId(gapId);
    try {
      await researchKnowledgeGap(agentId, gapId);
    } finally {
      setResearchingGapId(null);
      fetchAgentKnowledgeGaps(agentId).then(setGapsData);
    }
  }


  return (
    <>
      <div className="side-panel-overlay" onClick={onClose} />
      <aside className="side-panel" aria-label="Agent details">
        <div className="side-panel-header">
          <span className="badge">Agent detail</span>
          <button type="button" className="side-panel-close" aria-label="Close panel" onClick={onClose}>
            &times;
          </button>
        </div>
        {agent && (
          <>
            <div className="side-panel-title">
              <h2>{agent.name} <span className="badge">{agent.type}</span></h2>
            </div>
            <div className="side-panel-tabs" role="tablist">
              {(agent.type === 'expert' ? [...TABS, 'gaps' as const] : TABS).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab}
                  className={`side-panel-tab${activeTab === tab ? ' side-panel-tab--active' : ''}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {TAB_LABELS[tab]}
                </button>
              ))}
            </div>
          </>
        )}
        <div className="side-panel-body">
          {!agent && (
            <div className="side-panel-loading" data-testid="agent-detail-loading">
              <span className="side-panel-loading-spinner" aria-hidden="true" />
              Loading agent…
            </div>
          )}
          {agent && (
            <div className="side-panel-agent" data-agent-detail={agent.id}>
              {activeTab === 'overview' && (
                <div className="side-panel-section" data-testid="agent-overview-tab">
                  <h3>Overview</h3>
                  <div className="kv-list">
                    {agent.description && (
                      <div className="kv-row" data-testid="overview-description">
                        <span className="kv-key">Description</span>
                        <ExpandableText text={agent.description} />
                      </div>
                    )}
                    <div className="kv-row" data-testid="overview-purpose">
                      <span className="kv-key">Purpose</span>
                      <ExpandableText text={getAgentPurpose(agent)} />
                    </div>
                    <div className="kv-row" data-testid="overview-working-mode">
                      <span className="kv-key">Working mode</span>
                      <span>{WORKING_MODE_LABELS[agent.working_mode]}</span>
                    </div>
                    <div className="kv-row" data-testid="overview-guardrails">
                      <span className="kv-key">Guardrails</span>
                      <ExpandableText text={agent.guardrails || 'No guardrails set yet'} />
                    </div>
                    <div className="kv-row" data-testid="overview-scope">
                      <span className="kv-key">Vault scope</span>
                      <span>{agent.scope.length > 0 ? agent.scope.join(', ') : 'No vault scope assigned yet'}</span>
                    </div>
                    <div className="kv-row" data-testid="overview-tools">
                      <span className="kv-key">Tools</span>
                      <span>{agent.tools.length > 0 ? agent.tools.join(', ') : 'No tools enabled'}</span>
                    </div>
                    <div className="kv-row" data-testid="overview-depends-on">
                      <span className="kv-key">Relays to</span>
                      <span>{agent.depends_on.length > 0 ? agent.depends_on.join(', ') : 'Nothing — stands alone'}</span>
                    </div>
                    <div className="kv-row" data-testid="overview-preferred-indexes">
                      <span className="kv-key">Preferred indexes</span>
                      <span>
                        {agent.preferred_index_ids.length > 0
                          ? agent.preferred_index_ids.join(', ')
                          : 'None linked'}
                      </span>
                    </div>
                  </div>
                  {agent.type === 'expert' && (
                    <p className="text-muted" data-testid="overview-gap-count">
                      Open knowledge gaps: {gapsData?.open_count ?? 0}{' '}
                      <button
                        type="button"
                        className="btn"
                        onClick={() => setActiveTab('gaps')}
                        data-testid="overview-gap-count-link"
                      >
                        View
                      </button>
                    </p>
                  )}
                  <div className="side-panel-section-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => setActiveTab('chat')}
                      data-testid="overview-chat-link"
                    >
                      Chat with {agent.name}
                    </button>
                  </div>
                </div>
              )}

              {activeTab === 'settings' && (
                <>
                  <div className="side-panel-section">
                    <h3>Settings</h3>
                    <div className="kv-list">
                      {agent.settings.map((row) => (
                        <div className="kv-row" key={row.key}>
                          <span className="kv-key">{row.key}</span>
                          <span>{row.value}</span>
                        </div>
                      ))}
                      <div className="kv-row">
                        <span className="kv-key">Section</span>
                        {sections && (
                          <select
                            className="input kv-select"
                            value={agent.section_id}
                            onChange={(event) => handleSectionChange(event.target.value)}
                          >
                            {sections.map((section) => (
                              <option key={section.id} value={section.id}>{section.name}</option>
                            ))}
                          </select>
                        )}
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Provider</span>
                        {/* Read-only (2026-08-23) -- a Hermes agent's real
                            Provider comes straight from its own config.yaml
                            (agent.provider_name, ADR-004 point 3) and has no
                            real write path this panel can call: the old
                            editable dropdown was populated by GET /providers,
                            a Second-Brain-native registry endpoint that was
                            never rebuilt after the Hermes retrofit (a real
                            404 on every panel open), and even had it
                            resolved, agents_router.py's own PATCH body
                            (AgentVisualUpdateBody) never reads a provider_id
                            field at all -- selecting a different Provider
                            would have silently done nothing. */}
                        <span>{agent.provider_name || 'Unknown'}</span>
                      </div>
                      {!agent.provider_available && (
                        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
                          {agent.provider_name} has no real client built yet — this agent
                          honestly reports it's not available rather than silently falling
                          back to Compass.
                        </p>
                      )}
                      <div className="kv-row">
                        <span className="kv-key">Working mode</span>
                        {/* Read-only (2026-08-29) -- AgentManager.update() has
                            no working_mode parameter at all; this editable
                            dropdown sent a PATCH body field the backend
                            silently dropped and always returned the
                            hardcoded "autonomous" default regardless of what
                            was selected. No real per-agent store exists yet
                            (the intended real backing is Hermes' own
                            approval.request/respond mechanism, not yet
                            wired -- see AgentManager's own module docstring). */}
                        <span>{WORKING_MODE_LABELS[agent.working_mode]}</span>
                      </div>
                      <div className="kv-row" data-testid="background-agent-row">
                        <span className="kv-key">Background Agent</span>
                        <input
                          type="checkbox"
                          checked={agent.is_background_agent}
                          onChange={(event) => handleIsBackgroundAgentChange(event.target.checked)}
                        />
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Keywords</span>
                        {/* Read-only (2026-08-29) -- AgentManager.update()
                            has no keywords parameter at all; this editable
                            input sent a PATCH body field the backend
                            silently dropped, and to_detail_dict() always
                            returns [] regardless of what was typed here. No
                            real design/backing exists for this field yet. */}
                        <span className="text-muted">Not yet implemented</span>
                      </div>
                      <div className="kv-row" style={{ position: 'relative' }}>
                        <span className="kv-key">Vault scope</span>
                        <input
                          type="text"
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={scopeDraft}
                          onChange={(event) => setScopeDraft(event.target.value)}
                          onFocus={() => setScopeInputFocused(true)}
                          onBlur={() => {
                            handleScopeCommit();
                            setScopeInputFocused(false);
                          }}
                          placeholder="No vault scope assigned yet"
                          data-testid="vault-scope-input"
                        />
                        <button
                          type="button"
                          className="kv-expand-btn"
                          aria-label="Edit Vault scope in a bigger view"
                          data-testid="expand-vault-scope"
                          onClick={openScopeEditor}
                        >
                          <span className="material-symbols-outlined">open_in_full</span>
                        </button>
                        {scopeInputFocused && getFilteredScopeSuggestions().length > 0 && (
                          <ul
                            className="scope-suggestions-list"
                            data-testid="vault-scope-suggestions"
                            style={{
                              position: 'absolute',
                              top: '100%',
                              right: 0,
                              zIndex: 10,
                              listStyle: 'none',
                              margin: 0,
                              padding: 0,
                              background: 'var(--color-surface, #fff)',
                              border: '1px solid var(--color-border, #ccc)',
                            }}
                          >
                            {getFilteredScopeSuggestions().map((suggestion) => (
                              <li key={suggestion} data-testid="vault-scope-suggestion-item">
                                <button
                                  type="button"
                                  className="scope-suggestion-item"
                                  style={{ display: 'block', width: '100%', textAlign: 'left' }}
                                  // onMouseDown, NOT onClick -- fires before the input's
                                  // own onBlur={handleScopeCommit}, which would otherwise
                                  // already have committed scopeDraft/unmounted this list
                                  // before an onClick ever registered.
                                  onMouseDown={(event) => {
                                    event.preventDefault();
                                    handleScopeSuggestionSelect(suggestion);
                                  }}
                                >
                                  {suggestion}
                                </button>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Tools</span>
                        <input
                          type="text"
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={toolsDraft}
                          onChange={(event) => setToolsDraft(event.target.value)}
                          onBlur={handleToolsCommit}
                          placeholder="No tools enabled"
                          data-testid="tools-input"
                        />
                        <button
                          type="button"
                          className="kv-expand-btn"
                          aria-label="Edit Tools in a bigger view"
                          data-testid="expand-tools"
                          onClick={openToolsEditor}
                        >
                          <span className="material-symbols-outlined">open_in_full</span>
                        </button>
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Relays to</span>
                        <input
                          type="text"
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={dependsOnDraft}
                          onChange={(event) => setDependsOnDraft(event.target.value)}
                          onBlur={handleDependsOnCommit}
                          placeholder="Stands alone — no agent to relay to"
                          data-testid="depends-on-input"
                        />
                        <button
                          type="button"
                          className="kv-expand-btn"
                          aria-label="Edit Relays to in a bigger view"
                          data-testid="expand-depends-on"
                          onClick={openDependsOnEditor}
                        >
                          <span className="material-symbols-outlined">open_in_full</span>
                        </button>
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Preferred indexes</span>
                        <input
                          type="text"
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={preferredIndexIdsDraft}
                          onChange={(event) => setPreferredIndexIdsDraft(event.target.value)}
                          onBlur={handlePreferredIndexIdsCommit}
                          placeholder="None linked"
                          data-testid="preferred-index-ids-input"
                        />
                        <button
                          type="button"
                          className="kv-expand-btn"
                          aria-label="Edit Preferred indexes in a bigger view"
                          data-testid="expand-preferred-indexes"
                          onClick={openPreferredIndexesEditor}
                        >
                          <span className="material-symbols-outlined">open_in_full</span>
                        </button>
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Prompt</span>
                        <textarea
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={promptDraft}
                          onChange={(event) => setPromptDraft(event.target.value)}
                          onBlur={handlePromptCommit}
                          placeholder="No prompt override set — using the default"
                          data-testid="settings-prompt-input"
                        />
                        <button
                          type="button"
                          className="kv-expand-btn"
                          aria-label="Edit Prompt in a bigger view"
                          data-testid="expand-prompt"
                          onClick={() => setOpenFieldEditor('prompt')}
                        >
                          <span className="material-symbols-outlined">open_in_full</span>
                        </button>
                      </div>
                      <div className="kv-row">
                        <span className="kv-key">Guardrails</span>
                        <input
                          type="text"
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={guardrailsDraft}
                          onChange={(event) => setGuardrailsDraft(event.target.value)}
                          onBlur={handleGuardrailsCommit}
                          placeholder="No guardrails set yet"
                          data-testid="settings-guardrails-input"
                        />
                        <button
                          type="button"
                          className="kv-expand-btn"
                          aria-label="Edit Guardrails in a bigger view"
                          data-testid="expand-guardrails"
                          onClick={() => setOpenFieldEditor('guardrails')}
                        >
                          <span className="material-symbols-outlined">open_in_full</span>
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="side-panel-section">
                    <button
                      type="button"
                      className="section-collapse-header"
                      aria-expanded={capabilitiesExpanded}
                      data-testid="capabilities-collapse-toggle"
                      onClick={() => setCapabilitiesExpanded((expanded) => !expanded)}
                    >
                      <span className="section-collapse-title">Capabilities</span>
                      <span className="section-collapse-line" aria-hidden="true" />
                      <span className="section-collapse-arrow" aria-hidden="true">
                        {capabilitiesExpanded ? '▾' : '▸'}
                      </span>
                    </button>
                    {capabilitiesExpanded && (
                      <>
                        <div className="kv-list">
                          {agent.capabilities
                            .filter((capability) => capability.kind === 'action')
                            .map((capability) => (
                              <div className="kv-row" key={capability.id}>
                                <span className="kv-key">{capability.label}</span>
                                <span className="text-muted">Built-in</span>
                              </div>
                            ))}
                        </div>
                        {skillCatalog && (
                          <SkillsTree
                            mode="manage"
                            skills={buildSkillsTreeItems(skillCatalog, agent.capabilities)}
                            onGrantSkill={handleGrantSkill}
                            onGrantSkills={handleBulkGrantSkills}
                            onRevokeSkills={handleBulkRevokeSkills}
                          />
                        )}
                      </>
                    )}
                  </div>
                </>
              )}

              {activeTab === 'chat' && (
                <div className="side-panel-section side-panel-section--chat">
                  <AgentChatPanel
                    agentId={agentId}
                    agentName={agent.name}
                    onMessageSent={() => fetchAgentHistory(agentId).then(setHistory)}
                  />
                </div>
              )}

              {activeTab === 'history' && (
                <div className="side-panel-section">
                  <h3>Communication history</h3>
                  {history && history.length > 0 ? (
                    <div className="log-list">
                      {history.map((entry, index) =>
                        entry.kind === 'proposal' && entry.pending_approval_id ? (
                          <ProposalCard
                            key={index}
                            entry={entry}
                            approval={approvals[entry.pending_approval_id]}
                            onApprove={() => handleApprove(entry.pending_approval_id as string)}
                            onDecline={() => handleDecline(entry.pending_approval_id as string)}
                          />
                        ) : (
                          <div className="log-item" key={index}>
                            <span>{entry.text}</span>
                            <span className="log-item-meta">{entry.timestamp}</span>
                          </div>
                        ),
                      )}
                    </div>
                  ) : (
                    history && (
                      <div className="empty-state">
                        <p className="text-muted">Nothing recorded yet.</p>
                      </div>
                    )
                  )}

                  <h3 style={{ marginTop: 'var(--space-4)' }}>Hermes sessions</h3>
                  {hermesSessions === null ? (
                    <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>Loading...</p>
                  ) : hermesSessions.length === 0 ? (
                    <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }} data-testid="history-no-sessions">
                      No real Hermes sessions found for this agent yet.
                    </p>
                  ) : (
                    <div className="log-list" data-testid="history-hermes-sessions">
                      {hermesSessions.map((session) => (
                        <div className="log-item" key={session.id}>
                          <span>
                            {session.is_active ? (
                              <span className="badge badge-warning">Active</span>
                            ) : (
                              <span className="badge badge-success">Done</span>
                            )}{' '}
                            {session.title || '(untitled session)'} — {session.message_count} message
                            {session.message_count === 1 ? '' : 's'}
                            {session.ended_at !== null &&
                              ` — ${formatSessionDuration(session.started_at, session.ended_at)}`}
                          </span>
                          <span className="log-item-meta">{formatSessionTimestamp(session.started_at)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'schedule' && (
                <div className="side-panel-section" data-testid="agent-schedule-tab">
                  <h3>Schedule</h3>
                  <div className="kv-list">
                    <div className="kv-row">
                      <span className="kv-key">Capability</span>
                      <select
                        className="input kv-select"
                        value={scheduleCapabilityDraft}
                        onChange={(event) => setScheduleCapabilityDraft(event.target.value)}
                        data-testid="schedule-capability-select"
                      >
                        <option value="">Select a capability…</option>
                        {getSchedulableCapabilities().map((skill) => (
                          <option key={skill.id} value={skill.id}>{skill.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="kv-row">
                      <span className="kv-key">Interval</span>
                      <input
                        type="number"
                        className="input kv-select"
                        style={{ width: 90 }}
                        min={1}
                        value={scheduleIntervalValueDraft}
                        onChange={(event) => setScheduleIntervalValueDraft(event.target.value)}
                        data-testid="schedule-interval-value-input"
                      />
                      <select
                        className="input kv-select"
                        value={scheduleIntervalUnitDraft}
                        onChange={(event) =>
                          setScheduleIntervalUnitDraft(event.target.value as (typeof INTERVAL_UNITS)[number])
                        }
                        data-testid="schedule-interval-unit-select"
                      >
                        {INTERVAL_UNITS.map((unit) => (
                          <option key={unit} value={unit}>{unit}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  {scheduleError && (
                    <p className="text-muted" role="alert" data-testid="schedule-error">
                      {scheduleError}
                    </p>
                  )}
                  <div className="side-panel-section-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleScheduleSave}
                      disabled={scheduleSaving || !scheduleCapabilityDraft}
                      data-testid="schedule-save-button"
                    >
                      {scheduleEditingCapabilityId ? 'Save changes' : 'Create schedule'}
                    </button>
                    {scheduleEditingCapabilityId && (
                      <button type="button" className="btn" onClick={resetScheduleForm}>
                        Cancel edit
                      </button>
                    )}
                  </div>

                  <h3>Active schedules</h3>
                  {schedules && schedules.length > 0 ? (
                    <div className="log-list" data-testid="schedule-list">
                      {schedules.map((schedule) => (
                        <div className="log-item" key={schedule.capability_id} data-testid="schedule-item">
                          <span>
                            {agentSkills?.find((skill) => skill.id === schedule.capability_id)?.name ??
                              schedule.capability_id}{' '}
                            — every {schedule.interval_value} {schedule.interval_unit}
                          </span>
                          <div className="chat-proposal-actions">
                            <button type="button" className="btn" onClick={() => startEditSchedule(schedule)}>
                              Edit
                            </button>
                            <button
                              type="button"
                              className="btn btn-danger"
                              onClick={() => handleScheduleRemove(schedule.capability_id)}
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    schedules && (
                      <div className="empty-state">
                        <p className="text-muted">No active schedules yet.</p>
                      </div>
                    )
                  )}

                  <h3>Run now</h3>
                  <div className="side-panel-section-actions">
                    {getSchedulableCapabilities().map((skill) => (
                      <button
                        key={skill.id}
                        type="button"
                        className="btn"
                        onClick={() => handleRunScheduleNow(skill.id)}
                        disabled={runningNowCapabilityId === skill.id}
                        data-testid={`schedule-run-now-${skill.id}`}
                      >
                        {runningNowCapabilityId === skill.id ? 'Running…' : `Run now — ${skill.name}`}
                      </button>
                    ))}
                  </div>

                  <h3>Run history</h3>
                  {history && history.length > 0 ? (
                    <div className="log-list" data-testid="schedule-history-list">
                      {history.map((entry, index) => (
                        <div className="log-item" key={index}>
                          <span>{entry.text}</span>
                          <span className="log-item-meta">{entry.timestamp}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    history && (
                      <div className="empty-state">
                        <p className="text-muted">Nothing recorded yet.</p>
                      </div>
                    )
                  )}
                </div>
              )}

              {activeTab === 'visual' && (
                <div className="side-panel-section" data-testid="agent-visual-tab">
                  <h3>Visual</h3>
                  <VisualPicker
                    selectedIcon={agent.icon}
                    selectedColor={agent.color}
                    onSelectIcon={handleIconChange}
                    onSelectColor={handleColorChange}
                    onReset={handleVisualReset}
                  />
                </div>
              )}

              {activeTab === 'gaps' && agent.type === 'expert' && (
                <div className="side-panel-section" data-testid="knowledge-gaps-tab">
                  <h3>
                    Knowledge gaps{' '}
                    <span className="badge" data-testid="knowledge-gaps-open-count">
                      {gapsData?.open_count ?? 0} open
                    </span>
                  </h3>
                  {gapsData && gapsData.gaps.filter((gap) => gap.status === 'open').length > 0 ? (
                    <div className="log-list" data-testid="knowledge-gaps-list">
                      {gapsData.gaps
                        .filter((gap) => gap.status === 'open')
                        .map((gap) => (
                          <div className="log-item" key={gap.id} data-testid="knowledge-gap-item">
                            <p>{gap.question}</p>
                            <input
                              type="text"
                              className="input"
                              placeholder="Provide the missing information…"
                              value={gapAnswerDrafts[gap.id] ?? ''}
                              onChange={(event) =>
                                setGapAnswerDrafts((prev) => ({ ...prev, [gap.id]: event.target.value }))
                              }
                            />
                            <div className="chat-proposal-actions">
                              <button type="button" className="btn btn-primary" onClick={() => handleResolveGap(gap.id)}>
                                Submit answer
                              </button>
                              <button
                                type="button"
                                className="btn"
                                onClick={() => handleResearchGap(gap.id)}
                                disabled={researchingGapId === gap.id}
                              >
                                {researchingGapId === gap.id ? 'Researching…' : 'Research this'}
                              </button>
                            </div>
                          </div>
                        ))}
                    </div>
                  ) : (
                    gapsData && (
                      <div className="empty-state">
                        <p className="text-muted">No open knowledge gaps.</p>
                      </div>
                    )
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </aside>
      {openFieldEditor === 'prompt' && (
        <FieldEditorModal
          title="Prompt"
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          <textarea
            className="input field-editor-textarea"
            value={promptDraft}
            onChange={(event) => setPromptDraft(event.target.value)}
            placeholder="No prompt override set — using the default"
            data-testid="field-editor-prompt-textarea"
          />
        </FieldEditorModal>
      )}
      {openFieldEditor === 'guardrails' && (
        <FieldEditorModal
          title="Guardrails"
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          <textarea
            className="input field-editor-textarea"
            value={guardrailsDraft}
            onChange={(event) => setGuardrailsDraft(event.target.value)}
            placeholder="No guardrails set yet"
            data-testid="field-editor-guardrails-textarea"
          />
        </FieldEditorModal>
      )}
      {openFieldEditor === 'scope' && (
        <FieldEditorModal
          title="Vault scope"
          description="Real tags and folders from the vault — select every one this agent should be able to see."
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          {scopeSuggestions ? (
            <>
              <h4>Tags</h4>
              <TagTreePicker
                tags={scopeSuggestions.tags}
                selectedTags={scopeEditorDraft}
                onToggle={(tag) => toggleInDraft(setScopeEditorDraft, tag)}
              />
              <h4 style={{ marginTop: 'var(--space-4)' }}>Folders</h4>
              <ChecklistPicker
                items={scopeSuggestions.folders.map((folder): ChecklistItem => ({ id: folder, label: folder }))}
                selectedIds={scopeEditorDraft}
                onToggle={(folder) => toggleInDraft(setScopeEditorDraft, folder)}
                emptyLabel="No real vault folders found yet."
              />
            </>
          ) : (
            <p className="text-muted">Loading real tags and folders…</p>
          )}
        </FieldEditorModal>
      )}
      {openFieldEditor === 'tools' && (
        <FieldEditorModal
          title="Tools"
          description="Which real Hermes toolsets this agent is allowed to use."
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          {toolCatalog ? (
            <ChecklistPicker
              items={toolCatalog.map((name): ChecklistItem => ({ id: name, label: name }))}
              selectedIds={toolsEditorDraft}
              onToggle={(name) => toggleInDraft(setToolsEditorDraft, name)}
            />
          ) : (
            <p className="text-muted">Loading the real toolset catalog…</p>
          )}
        </FieldEditorModal>
      )}
      {openFieldEditor === 'dependsOn' && (
        <FieldEditorModal
          title="Relays to"
          description="Which other real agents this agent can hand a request up to."
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          {agentCatalog ? (
            <ChecklistPicker
              items={agentCatalog
                .filter((candidate) => candidate.id !== agentId)
                .map((candidate): ChecklistItem => ({ id: candidate.id, label: candidate.name, meta: candidate.type }))}
              selectedIds={dependsOnEditorDraft}
              onToggle={(id) => toggleInDraft(setDependsOnEditorDraft, id)}
            />
          ) : (
            <p className="text-muted">Loading the real agent list…</p>
          )}
        </FieldEditorModal>
      )}
      {openFieldEditor === 'preferredIndexes' && (
        <FieldEditorModal
          title="Preferred indexes"
          description="Which real Indexes this agent should consult first when looking for vault data."
          onClose={() => setOpenFieldEditor(null)}
          onSave={handleSaveFieldEditor}
          saving={savingFieldEditor}
        >
          {indexCatalog ? (
            <ChecklistPicker
              items={indexCatalog.map((index): ChecklistItem => ({ id: index.id, label: index.name }))}
              selectedIds={preferredIndexIdsEditorDraft}
              onToggle={(id) => toggleInDraft(setPreferredIndexIdsEditorDraft, id)}
              emptyLabel="No real Indexes exist yet."
            />
          ) : (
            <p className="text-muted">Loading the real Index catalog…</p>
          )}
        </FieldEditorModal>
      )}
    </>
  );
}

function ProposalCard({
  entry,
  approval,
  onApprove,
  onDecline,
}: {
  entry: AgentHistoryEntry;
  approval: PendingApproval | undefined;
  onApprove: () => void;
  onDecline: () => void;
}) {
  const status = approval?.status ?? 'pending';
  if (status === 'approved') {
    return (
      <div className="chat-proposal chat-proposal--approved">
        <span className="badge badge-success">Approved</span>
        <p>{entry.text}</p>
      </div>
    );
  }
  if (status === 'declined') {
    return (
      <div className="chat-proposal chat-proposal--declined">
        <span className="badge badge-danger">Declined</span>
        <p>{entry.text}</p>
      </div>
    );
  }
  return (
    <div className="chat-proposal">
      <span className="badge badge-warning">Awaiting your approval</span>
      <p>{entry.text}</p>
      <div className="chat-proposal-actions">
        <button type="button" className="btn btn-primary" onClick={onApprove}>Approve</button>
        <button type="button" className="btn btn-danger" onClick={onDecline}>Decline</button>
      </div>
    </div>
  );
}
