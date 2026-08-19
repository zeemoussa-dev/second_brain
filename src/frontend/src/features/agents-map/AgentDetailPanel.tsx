import { useEffect, useRef, useState } from 'react';
import {
  fetchAgent,
  fetchAgentHistory,
  fetchAgentKnowledgeGaps,
  researchKnowledgeGap,
  resolveKnowledgeGap,
  sendChatMessage,
  sendChatMessageWithAttachment,
  updateAgentAssignment,
  type AgentDetail,
  type AgentHistoryEntry,
  type KnowledgeGapsResponse,
} from './agentsApiClient';
import { fetchSections, fetchProviders, type SectionSummary, type ProviderSummary } from '../settings/settingsApiClient';
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
import { ChatMessageText } from '../../components/ChatMessageText';

interface AgentDetailPanelProps {
  agentId: string;
  onClose: () => void;
}

interface ChatMessage {
  role: 'user' | 'agent';
  text: string;
  isError?: boolean;
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
  return 'No stated purpose recorded for this agent.';
}

const WORKING_MODE_LABELS: Record<AgentDetail['working_mode'], string> = {
  autonomous: 'Autonomous',
  supervised: 'Supervised',
  manual: 'Manual',
};

const GUARDRAILS_STATEMENT =
  "Replies are grounded in what this agent's own tools actually find in the vault — it honestly says it doesn't know rather than guessing.";

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

const ACCEPTED_EXTENSIONS = ['.pdf', '.txt', '.md'];

export function AgentDetailPanel({ agentId, onClose }: AgentDetailPanelProps) {
  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [history, setHistory] = useState<AgentHistoryEntry[] | null>(null);
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  const [providers, setProviders] = useState<ProviderSummary[] | null>(null);
  const [skillCatalog, setSkillCatalog] = useState<SkillSummary[] | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [keywordsDraft, setKeywordsDraft] = useState('');
  const [scopeDraft, setScopeDraft] = useState('');
  const [promptDraft, setPromptDraft] = useState('');
  const [guardrailsDraft, setGuardrailsDraft] = useState('');
  const [scopeSuggestions, setScopeSuggestions] = useState<ScopeSuggestions | null>(null);
  const [approvals, setApprovals] = useState<Record<string, PendingApproval>>({});
  const [gapsData, setGapsData] = useState<KnowledgeGapsResponse | null>(null);
  const [gapAnswerDrafts, setGapAnswerDrafts] = useState<Record<string, string>>({});
  const [researchingGapId, setResearchingGapId] = useState<string | null>(null);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [attachError, setAttachError] = useState<string | null>(null);
  const [schedules, setSchedules] = useState<AgentSchedule[] | null>(null);
  const [agentSkills, setAgentSkills] = useState<SkillSummary[] | null>(null);
  const [scheduleEditingCapabilityId, setScheduleEditingCapabilityId] = useState<string | null>(null);
  const [scheduleCapabilityDraft, setScheduleCapabilityDraft] = useState('');
  const [scheduleIntervalValueDraft, setScheduleIntervalValueDraft] = useState('60');
  const [scheduleIntervalUnitDraft, setScheduleIntervalUnitDraft] = useState<(typeof INTERVAL_UNITS)[number]>('minutes');
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const [scheduleSaving, setScheduleSaving] = useState(false);
  const [runningNowCapabilityId, setRunningNowCapabilityId] = useState<string | null>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setAgent(null); // clear stale content immediately on agent switch
    setMessages([]); // clear the previous agent's chat thread on switch
    setDraft('');
    setSending(false);
    setHistory(null); // clear the previous agent's history on switch
    setActiveTab('overview');
    setKeywordsDraft('');
    setScopeDraft('');
    setPromptDraft('');
    setGuardrailsDraft('');
    setScopeSuggestions(null); // clear the previous agent's suggestion snapshot on switch
    setGapsData(null);
    setGapAnswerDrafts({});
    setResearchingGapId(null);
    setAttachedFile(null); // clear the previous agent's staged attachment on switch
    setAttachError(null);
    setSchedules(null); // clear the previous agent's schedules on switch
    setAgentSkills(null);
    setScheduleEditingCapabilityId(null);
    setScheduleCapabilityDraft('');
    setScheduleIntervalValueDraft('60');
    setScheduleIntervalUnitDraft('minutes');
    setScheduleError(null);
    fetchAgent(agentId).then((detail) => {
      setAgent(detail);
      setKeywordsDraft(detail.keywords.join(', '));
      setScopeDraft(detail.scope.join(', '));
      setPromptDraft(detail.prompt ?? '');
      setGuardrailsDraft(detail.guardrails);
    });
    fetchAgentHistory(agentId).then(setHistory);
    fetchSections().then(setSections);
    fetchProviders().then(setProviders);
    fetchSkills().then(setSkillCatalog);
    fetchScopeSuggestions().then(setScopeSuggestions);
  }, [agentId]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, sending]);

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
  }

  async function handleProviderChange(providerId: string) {
    const updated = await updateAgentAssignment(agentId, { provider_id: providerId });
    setAgent(updated);
  }

  async function handleWorkingModeChange(workingMode: string) {
    const updated = await updateAgentAssignment(agentId, { working_mode: workingMode });
    setAgent(updated);
  }

  async function handleIsBackgroundAgentChange(isBackgroundAgent: boolean) {
    const updated = await updateAgentAssignment(agentId, { is_background_agent: isBackgroundAgent });
    setAgent(updated);
  }

  async function handleIconChange(iconId: string) {
    const updated = await updateAgentAssignment(agentId, { icon: iconId });
    setAgent(updated);
  }

  async function handleColorChange(colorHex: string) {
    const updated = await updateAgentAssignment(agentId, { color: colorHex });
    setAgent(updated);
  }

  async function handleVisualReset() {
    // "" is the backend's own clear-to-default sentinel
    // (agent_visual_registry.py) — distinct from omitting the field.
    const updated = await updateAgentAssignment(agentId, { icon: '', color: '' });
    setAgent(updated);
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
  }

  async function handleRevokeSkill(skillId: string) {
    await revokeAgentSkill(agentId, skillId);
    const updated = await fetchAgent(agentId);
    setAgent(updated);
  }

  // Multi-select bulk actions (REQ-SB-48-US-01-T02) -- N sequential calls to
  // the same single-Skill grantAgentSkill/revokeAgentSkill primitive
  // handleGrantSkill/handleRevokeSkill above already use, never a new batch
  // endpoint; one combined refetch after the whole batch rather than one per
  // Skill (handleGrantSkill/handleRevokeSkill themselves stay unchanged, so
  // the existing per-row Grant/Revoke buttons keep their exact prior
  // behavior).
  async function handleBulkGrantSkills(skillIds: string[]) {
    for (const skillId of skillIds) {
      await grantAgentSkill(agentId, skillId);
    }
    const updated = await fetchAgent(agentId);
    setAgent(updated);
  }

  async function handleBulkRevokeSkills(skillIds: string[]) {
    for (const skillId of skillIds) {
      await revokeAgentSkill(agentId, skillId);
    }
    const updated = await fetchAgent(agentId);
    setAgent(updated);
  }

  async function handleKeywordsCommit() {
    const keywords = keywordsDraft
      .split(',')
      .map((keyword) => keyword.trim())
      .filter((keyword) => keyword.length > 0);
    const updated = await updateAgentAssignment(agentId, { keywords });
    setAgent(updated);
    setKeywordsDraft(updated.keywords.join(', '));
  }

  async function handleScopeCommit() {
    const scope = scopeDraft
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    const updated = await updateAgentAssignment(agentId, { scope });
    setAgent(updated);
    setScopeDraft(updated.scope.join(', '));
  }

  async function handlePromptCommit() {
    const updated = await updateAgentAssignment(agentId, { prompt: promptDraft });
    setAgent(updated);
    setPromptDraft(updated.prompt ?? '');
  }

  async function handleGuardrailsCommit() {
    const updated = await updateAgentAssignment(agentId, { guardrails: guardrailsDraft });
    setAgent(updated);
    setGuardrailsDraft(updated.guardrails);
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

  function handleFileSelect(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const extension = `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`;
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setAttachError(
        `'${extension}' files aren't supported yet — only PDF (.pdf), plain text (.txt), and Markdown (.md) files can be summarized today.`,
      );
      setAttachedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    setAttachError(null);
    setAttachedFile(file);
  }

  function handleRemoveAttachment() {
    setAttachedFile(null);
    setAttachError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if ((!text && !attachedFile) || sending) return;
    const bubbleText = attachedFile ? `${text} [attached: ${attachedFile.name}]`.trim() : text;
    setMessages((prev) => [...prev, { role: 'user', text: bubbleText }]);
    setDraft('');
    const fileToSend = attachedFile;
    setAttachedFile(null);
    setAttachError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setSending(true);
    try {
      if (fileToSend) {
        const response = await sendChatMessageWithAttachment(agentId, text, fileToSend);
        setMessages((prev) => [
          ...prev,
          { role: 'agent', text: response.reply, isError: response.attachment_status === 'rejected' },
        ]);
      } else {
        const response = await sendChatMessage(agentId, text);
        setMessages((prev) => [...prev, { role: 'agent', text: response.reply }]);
      }
      fetchAgentHistory(agentId).then(setHistory);
    } catch {
      // A real Compass-backed reply can genuinely fail (network error,
      // Provider timeout) -- surfaced honestly in the thread itself, not
      // silently dropped, matching this project's own "honest, not
      // fabricated/swallowed" posture already established for actions.
      setMessages((prev) => [
        ...prev,
        { role: 'agent', text: 'Something went wrong sending that message. Please try again.', isError: true },
      ]);
    } finally {
      setSending(false);
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
          {agent && (
            <div className="side-panel-agent" data-agent-detail={agent.id}>
              {activeTab === 'overview' && (
                <div className="side-panel-section" data-testid="agent-overview-tab">
                  <h3>Overview</h3>
                  <div className="kv-list">
                    <div className="kv-row" data-testid="overview-purpose">
                      <span className="kv-key">Purpose</span>
                      <span>{getAgentPurpose(agent)}</span>
                    </div>
                    <div className="kv-row" data-testid="overview-working-mode">
                      <span className="kv-key">Working mode</span>
                      <span>{WORKING_MODE_LABELS[agent.working_mode]}</span>
                    </div>
                    <div className="kv-row" data-testid="overview-guardrails">
                      <span className="kv-key">Guardrails</span>
                      <span>{GUARDRAILS_STATEMENT}</span>
                    </div>
                    <div className="kv-row" data-testid="overview-scope">
                      <span className="kv-key">Vault scope</span>
                      <span>{agent.scope.length > 0 ? agent.scope.join(', ') : 'No vault scope assigned yet'}</span>
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
                        {providers && (
                          <select
                            className="input kv-select"
                            value={agent.provider_id}
                            onChange={(event) => handleProviderChange(event.target.value)}
                          >
                            {providers.map((provider) => (
                              <option key={provider.id} value={provider.id}>
                                {provider.name}{provider.is_default ? ' (default)' : ''}
                              </option>
                            ))}
                          </select>
                        )}
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
                        <select
                          className="input kv-select"
                          value={agent.working_mode}
                          onChange={(event) => handleWorkingModeChange(event.target.value)}
                        >
                          <option value="autonomous">Autonomous</option>
                          <option value="supervised">Supervised</option>
                          <option value="manual">Manual</option>
                        </select>
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
                        <input
                          type="text"
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={keywordsDraft}
                          onChange={(event) => setKeywordsDraft(event.target.value)}
                          onBlur={handleKeywordsCommit}
                          placeholder="No keywords assigned yet"
                        />
                      </div>
                      <div className="kv-row" style={{ position: 'relative' }}>
                        <span className="kv-key">Vault scope</span>
                        <input
                          type="text"
                          className="input kv-select"
                          style={{ minWidth: 220 }}
                          value={scopeDraft}
                          onChange={(event) => setScopeDraft(event.target.value)}
                          onBlur={handleScopeCommit}
                          placeholder="No vault scope assigned yet"
                          data-testid="vault-scope-input"
                        />
                        {getFilteredScopeSuggestions().length > 0 && (
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
                      </div>
                    </div>
                  </div>

                  <div className="side-panel-section">
                    <h3>Capabilities</h3>
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
                        onRevokeSkill={handleRevokeSkill}
                        onGrantSkills={handleBulkGrantSkills}
                        onRevokeSkills={handleBulkRevokeSkills}
                      />
                    )}
                  </div>
                </>
              )}

              {activeTab === 'chat' && (
                <div className="side-panel-section side-panel-section--chat">
                  <div className="chat-thread" data-role="agent-chat-thread">
                    {messages.length === 0 && (
                      <p className="text-muted chat-thread-empty">
                        Ask {agent.name} anything, or send one of its known trigger
                        phrases to run an action directly.
                      </p>
                    )}
                    {messages.map((message, index) => (
                      <div
                        className={`chat-message chat-message--${message.role}${message.isError ? ' chat-message--error' : ''}`}
                        key={index}
                      >
                        <ChatMessageText text={message.text} />
                      </div>
                    ))}
                    {sending && (
                      <div className="chat-message chat-message--agent chat-message--pending" aria-live="polite">
                        <span className="chat-typing-dot" />
                        <span className="chat-typing-dot" />
                        <span className="chat-typing-dot" />
                      </div>
                    )}
                    <div ref={threadEndRef} />
                  </div>
                  {attachError && (
                    <p className="text-muted" data-role="chat-attach-error" role="alert">
                      {attachError}
                    </p>
                  )}
                  {attachedFile && (
                    <div className="chat-attach-preview" data-role="chat-attach-preview">
                      <span>📎 {attachedFile.name}</span>
                      <button type="button" className="btn" onClick={handleRemoveAttachment}>
                        Remove
                      </button>
                    </div>
                  )}
                  <form className="chat-input-row" onSubmit={handleSend}>
                    <input
                      type="text"
                      className="input"
                      placeholder={`Message ${agent.name}…`}
                      value={draft}
                      onChange={(event) => setDraft(event.target.value)}
                      disabled={sending}
                    />
                    <input
                      type="file"
                      accept=".pdf,.txt,.md"
                      data-role="chat-attach-input"
                      aria-label="Attach file"
                      ref={fileInputRef}
                      onChange={handleFileSelect}
                      disabled={sending}
                    />
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={sending || (!draft.trim() && !attachedFile)}
                    >
                      {sending ? 'Sending…' : 'Send'}
                    </button>
                  </form>
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
