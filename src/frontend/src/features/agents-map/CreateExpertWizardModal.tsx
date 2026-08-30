import { useEffect, useState } from 'react';
import { ApiError } from '../../api/client';
import { fetchSections, type SectionSummary } from '../settings/settingsApiClient';
import { fetchScopeSuggestions, type ScopeSuggestions } from '../vault-browser/client';
import { fetchIndexes, type IndexSummary } from './indexesApiClient';
import { fetchToolCatalog } from './toolsApiClient';
import { fetchSkills, grantAgentSkill, type SkillSummary } from './skillsApiClient';
import { createAgent, fetchAgent, updateAgentAssignment, type AgentDetail } from './agentsApiClient';
import { ChecklistPicker, type ChecklistItem } from './ChecklistPicker';
import { TagTreePicker } from './TagTreePicker';
import { VisualPicker } from './VisualPicker';
import { SkillsTree } from './SkillsTree';
import { getVisualIconName } from './visualOptions';

interface CreateExpertWizardModalProps {
  onClose: () => void;
  onCreated: (agent: AgentDetail) => void;
}

// A real slug, always -- the id input's own onChange runs every
// keystroke through this rather than validating-then-rejecting, so the
// field can never hold something the backend (a real Hermes profile
// folder name) would refuse. Auto-derived from Name until the operator
// types into the Id field directly (`idTouched`), same "auto-slug until
// you touch it yourself" convention most apps with a derived-slug field
// use.
function slugify(input: string): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Icon reused in both the step-bar circle AND that step's own in-body
// heading (operator: "how to use Icons when possible or needed") -- one
// source of truth per step so the two never drift apart.
interface WizardStepConfig {
  key: 'identity' | 'knowledge' | 'tools' | 'behavior' | 'appearance' | 'review';
  title: string;
  subtitle: string;
  icon: string;
}

const WIZARD_STEPS: WizardStepConfig[] = [
  { key: 'identity', title: 'Identity', subtitle: 'Who this Expert is, and where it lives on the map', icon: 'badge' },
  { key: 'knowledge', title: 'Knowledge & access', subtitle: 'What this Expert can see in the vault', icon: 'database' },
  { key: 'tools', title: 'Tools & skills', subtitle: 'What this Expert is allowed to do', icon: 'build' },
  { key: 'behavior', title: 'Behavior', subtitle: 'How this Expert should act', icon: 'tune' },
  { key: 'appearance', title: 'Appearance', subtitle: 'How this Expert shows up on the map', icon: 'palette' },
  { key: 'review', title: 'Review', subtitle: 'Check everything before creating it for real', icon: 'check_circle' },
];

export function CreateExpertWizardModal({ onClose, onCreated }: CreateExpertWizardModalProps) {
  const [stepIndex, setStepIndex] = useState(0);
  const step = WIZARD_STEPS[stepIndex];

  // Step 1 -- Identity.
  const [name, setName] = useState('');
  const [id, setId] = useState('');
  const [idTouched, setIdTouched] = useState(false);
  const [sectionId, setSectionId] = useState('');
  const [description, setDescription] = useState('');
  const [identityError, setIdentityError] = useState<string | null>(null);

  // Step 2 -- Knowledge & access.
  const [scopeSelected, setScopeSelected] = useState<string[]>([]);
  const [preferredIndexIds, setPreferredIndexIds] = useState<string[]>([]);

  // Step 3 -- Tools & skills.
  const [toolsSelected, setToolsSelected] = useState<string[]>([]);
  const [skillsSelected, setSkillsSelected] = useState<string[]>([]);

  // Step 4 -- Behavior.
  const [prompt, setPrompt] = useState('');
  const [guardrails, setGuardrails] = useState('');
  const [isBackgroundAgent, setIsBackgroundAgent] = useState(false);

  // Step 5 -- Appearance.
  const [icon, setIcon] = useState<string | null>(null);
  const [color, setColor] = useState<string | null>(null);

  // Step 6 -- Review/submit.
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Every real catalog this wizard needs, fetched once up front on open
  // -- a wizard reads badly with a fresh spinner every time you land on
  // a new step, so all 5 load together while Step 1 (nothing to fetch)
  // is already interactive.
  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  const [scopeSuggestions, setScopeSuggestions] = useState<ScopeSuggestions | null>(null);
  const [indexes, setIndexes] = useState<IndexSummary[] | null>(null);
  const [tools, setTools] = useState<string[] | null>(null);
  const [skills, setSkills] = useState<SkillSummary[] | null>(null);

  useEffect(() => {
    fetchSections().then(setSections);
    fetchScopeSuggestions().then(setScopeSuggestions);
    fetchIndexes().then(setIndexes);
    fetchToolCatalog().then(setTools);
    fetchSkills().then(setSkills);
  }, []);

  function handleNameChange(value: string) {
    setName(value);
    if (!idTouched) setId(slugify(value));
  }

  function toggleScope(value: string) {
    setScopeSelected((current) =>
      current.includes(value) ? current.filter((entry) => entry !== value) : [...current, value],
    );
  }

  function togglePreferredIndex(value: string) {
    setPreferredIndexIds((current) =>
      current.includes(value) ? current.filter((entry) => entry !== value) : [...current, value],
    );
  }

  function toggleTool(value: string) {
    setToolsSelected((current) =>
      current.includes(value) ? current.filter((entry) => entry !== value) : [...current, value],
    );
  }

  function validateIdentity(): string | null {
    if (!name.trim()) return 'a name';
    if (!id) return 'an id';
    if (!sectionId) return 'a Section';
    return null;
  }

  function handleIdentityNext() {
    const missing = validateIdentity();
    if (missing) {
      setIdentityError(`Missing ${missing} — Next is disabled until this step is complete.`);
      return;
    }
    setIdentityError(null);
    setStepIndex(1);
  }

  function goBack() {
    setStepIndex((current) => Math.max(0, current - 1));
  }

  function goNext() {
    setStepIndex((current) => Math.min(WIZARD_STEPS.length - 1, current + 1));
  }

  async function handleCreate() {
    const missing = validateIdentity();
    if (missing) {
      setSubmitError(`Missing ${missing} — go back to Identity to fix it.`);
      return;
    }
    setSubmitError(null);
    setSubmitting(true);
    try {
      let agent = await createAgent({
        id,
        name: name.trim(),
        section_id: sectionId,
        type: 'expert',
        is_background_agent: isBackgroundAgent,
        description: description.trim() || undefined,
        prompt: prompt.trim() || undefined,
        guardrails: guardrails.trim() || undefined,
        scope: scopeSelected.length > 0 ? scopeSelected : undefined,
        preferred_index_ids: preferredIndexIds.length > 0 ? preferredIndexIds : undefined,
        tools: toolsSelected.length > 0 ? toolsSelected : undefined,
      });
      if (icon || color) {
        agent = await updateAgentAssignment(agent.id, {
          icon: icon ?? undefined,
          color: color ?? undefined,
        });
      }
      for (const skillId of skillsSelected) {
        await grantAgentSkill(agent.id, skillId);
      }
      if (skillsSelected.length > 0) {
        agent = await fetchAgent(agent.id);
      }
      onCreated(agent);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong — the agent was not created.',
      );
    } finally {
      setSubmitting(false);
    }
  }

  const sectionNameById = (value: string) => sections?.find((section) => section.id === value)?.name ?? value;
  const indexNameById = (value: string) => indexes?.find((entry) => entry.id === value)?.name ?? value;
  const skillNameById = (value: string) => skills?.find((entry) => entry.id === value)?.name ?? value;
  const iconLigature = getVisualIconName(icon);

  return (
    <div className="wizard-modal-overlay" data-testid="expert-wizard-overlay" onClick={onClose}>
      <div
        className="wizard-modal wizard-modal--wide"
        data-testid="expert-wizard-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="wizard-modal-header">
          <h2>
            <span className="material-symbols-outlined wizard-modal-header-icon" aria-hidden="true">psychology</span>
            Create Expert
          </h2>
          <button
            type="button"
            className="wizard-modal-close"
            data-testid="expert-wizard-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="wizard-step-bar" data-testid="expert-wizard-step-bar">
          {WIZARD_STEPS.map((stepConfig, index) => (
            <div className="wizard-step-item" key={stepConfig.key}>
              <div
                className={`wizard-step${index === stepIndex ? ' wizard-step--current' : ''}${index < stepIndex ? ' wizard-step--done' : ''}`}
                data-testid={`expert-wizard-step-${stepConfig.key}`}
                aria-current={index === stepIndex ? 'step' : undefined}
                title={stepConfig.title}
              >
                <span className="material-symbols-outlined" aria-hidden="true">
                  {index < stepIndex ? 'check' : stepConfig.icon}
                </span>
              </div>
              {index < WIZARD_STEPS.length - 1 && <div className="wizard-step-connector" aria-hidden="true" />}
            </div>
          ))}
        </div>
        <div className="wizard-modal-body">
          <div className="wizard-step-heading">
            <span className="material-symbols-outlined wizard-step-heading-icon" aria-hidden="true">{step.icon}</span>
            <div>
              <h3>{step.title}</h3>
              <p className="text-muted">{step.subtitle}</p>
            </div>
          </div>

          {step.key === 'identity' && (
            <div data-testid="expert-wizard-step-identity-body">
              {identityError && (
                <p className="text-muted" data-testid="expert-wizard-identity-error">
                  <span className="badge badge-danger">Can't continue</span> {identityError}
                </p>
              )}
              <label className="text-muted" htmlFor="expertWizardName">Name</label>
              <input
                id="expertWizardName"
                className="input"
                data-testid="expert-wizard-name-input"
                value={name}
                onChange={(event) => handleNameChange(event.target.value)}
                placeholder="e.g. Retail Expert"
                autoFocus
              />
              <label className="text-muted" htmlFor="expertWizardId">
                Id <span className="text-muted">(the real profile folder name — auto-filled from Name)</span>
              </label>
              <input
                id="expertWizardId"
                className="input"
                data-testid="expert-wizard-id-input"
                value={id}
                onChange={(event) => {
                  setIdTouched(true);
                  setId(slugify(event.target.value));
                }}
                placeholder="e.g. retail-expert"
              />
              <label className="text-muted" htmlFor="expertWizardSection">Section</label>
              <select
                id="expertWizardSection"
                className="input"
                data-testid="expert-wizard-section-select"
                value={sectionId}
                onChange={(event) => setSectionId(event.target.value)}
              >
                <option value="">Choose a Section…</option>
                {sections?.map((section) => (
                  <option key={section.id} value={section.id}>{section.name}</option>
                ))}
              </select>
              <label className="text-muted" htmlFor="expertWizardDescription">Description</label>
              <textarea
                id="expertWizardDescription"
                className="input"
                data-testid="expert-wizard-description-input"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="What is this Expert's own knowledge domain?"
                rows={3}
              />
            </div>
          )}

          {step.key === 'knowledge' && (
            <div data-testid="expert-wizard-step-knowledge-body">
              <h4>Vault scope</h4>
              {scopeSuggestions ? (
                <>
                  <p className="text-muted">Tags</p>
                  <TagTreePicker
                    tags={scopeSuggestions.tags}
                    selectedTags={scopeSelected}
                    onToggle={toggleScope}
                  />
                  <p className="text-muted" style={{ marginTop: 'var(--space-4)' }}>Folders</p>
                  <ChecklistPicker
                    items={scopeSuggestions.folders.map((folder): ChecklistItem => ({ id: folder, label: folder }))}
                    selectedIds={scopeSelected}
                    onToggle={toggleScope}
                    emptyLabel="No real vault folders found yet."
                  />
                </>
              ) : (
                <p className="text-muted">Loading real tags and folders…</p>
              )}
              <h4 style={{ marginTop: 'var(--space-5)' }}>Preferred indexes</h4>
              {indexes ? (
                <ChecklistPicker
                  items={indexes.map((entry): ChecklistItem => ({ id: entry.id, label: entry.name }))}
                  selectedIds={preferredIndexIds}
                  onToggle={togglePreferredIndex}
                  emptyLabel="No real Indexes exist yet."
                />
              ) : (
                <p className="text-muted">Loading the real Index catalog…</p>
              )}
            </div>
          )}

          {step.key === 'tools' && (
            <div data-testid="expert-wizard-step-tools-body">
              <h4>Tools</h4>
              {tools ? (
                <ChecklistPicker
                  items={tools.map((name): ChecklistItem => ({ id: name, label: name }))}
                  selectedIds={toolsSelected}
                  onToggle={toggleTool}
                />
              ) : (
                <p className="text-muted">Loading the real toolset catalog…</p>
              )}
              <h4 style={{ marginTop: 'var(--space-5)' }}>Skills</h4>
              {skills ? (
                <SkillsTree
                  mode="select"
                  skills={skills.map((skill) => ({ id: skill.id, name: skill.name, tool: skill.tool, granted: false }))}
                  selectedIds={skillsSelected}
                  onChange={setSkillsSelected}
                />
              ) : (
                <p className="text-muted">Loading the real Skill catalog…</p>
              )}
            </div>
          )}

          {step.key === 'behavior' && (
            <div data-testid="expert-wizard-step-behavior-body">
              <label className="text-muted" htmlFor="expertWizardPrompt">Prompt</label>
              <textarea
                id="expertWizardPrompt"
                className="input"
                data-testid="expert-wizard-prompt-input"
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Extra instructions woven into this Expert's own SOUL.md"
                rows={4}
              />
              <label className="text-muted" htmlFor="expertWizardGuardrails">Guardrails</label>
              <textarea
                id="expertWizardGuardrails"
                className="input"
                data-testid="expert-wizard-guardrails-input"
                value={guardrails}
                onChange={(event) => setGuardrails(event.target.value)}
                placeholder="What this Expert should never do"
                rows={4}
              />
              <label className="text-muted">
                <input
                  type="checkbox"
                  data-testid="expert-wizard-background-checkbox"
                  checked={isBackgroundAgent}
                  onChange={(event) => setIsBackgroundAgent(event.target.checked)}
                />
                {' '}Background agent (runs without a direct chat surface)
              </label>
            </div>
          )}

          {step.key === 'appearance' && (
            <div data-testid="expert-wizard-step-appearance-body">
              <VisualPicker
                selectedIcon={icon}
                selectedColor={color}
                onSelectIcon={setIcon}
                onSelectColor={setColor}
                onReset={() => {
                  setIcon(null);
                  setColor(null);
                }}
              />
            </div>
          )}

          {step.key === 'review' && (
            <div data-testid="expert-wizard-step-review-body">
              <div className="wizard-review-preview">
                <span
                  className="wizard-review-preview-dot"
                  style={color ? { background: color, borderColor: color } : undefined}
                >
                  {iconLigature && (
                    <span className="material-symbols-outlined" aria-hidden="true">{iconLigature}</span>
                  )}
                </span>
                <div>
                  <p className="wizard-review-preview-name">{name || 'Untitled Expert'}</p>
                  <p className="text-muted">{id || '—'} · {sectionId ? sectionNameById(sectionId) : 'No Section chosen'}</p>
                </div>
              </div>
              <div className="kv-list" data-testid="expert-wizard-summary">
                <div className="kv-row"><span className="kv-key">Description</span><span>{description || '—'}</span></div>
                <div className="kv-row">
                  <span className="kv-key">Vault scope</span>
                  <span>{scopeSelected.length > 0 ? scopeSelected.join(', ') : 'None'}</span>
                </div>
                <div className="kv-row">
                  <span className="kv-key">Preferred indexes</span>
                  <span>{preferredIndexIds.length > 0 ? preferredIndexIds.map(indexNameById).join(', ') : 'None'}</span>
                </div>
                <div className="kv-row">
                  <span className="kv-key">Tools</span>
                  <span>{toolsSelected.length > 0 ? toolsSelected.join(', ') : 'None'}</span>
                </div>
                <div className="kv-row">
                  <span className="kv-key">Skills</span>
                  <span>{skillsSelected.length > 0 ? skillsSelected.map(skillNameById).join(', ') : 'None'}</span>
                </div>
                <div className="kv-row"><span className="kv-key">Prompt</span><span>{prompt || '—'}</span></div>
                <div className="kv-row"><span className="kv-key">Guardrails</span><span>{guardrails || '—'}</span></div>
                <div className="kv-row"><span className="kv-key">Background agent</span><span>{isBackgroundAgent ? 'Yes' : 'No'}</span></div>
              </div>
              {submitError && (
                <p className="text-muted" data-testid="expert-wizard-submit-error">
                  <span className="badge badge-danger">Can't create agent</span> {submitError}
                </p>
              )}
            </div>
          )}

          <div className="item-row-actions wizard-step-footer">
            {stepIndex > 0 && (
              <button type="button" className="btn" data-testid="expert-wizard-back" onClick={goBack}>
                Back
              </button>
            )}
            {step.key === 'identity' && (
              <button type="button" className="btn btn-primary" data-testid="expert-wizard-next" onClick={handleIdentityNext}>
                Next
              </button>
            )}
            {step.key !== 'identity' && step.key !== 'review' && (
              <button type="button" className="btn btn-primary" data-testid="expert-wizard-next" onClick={goNext}>
                Next
              </button>
            )}
            {step.key === 'review' && (
              <button
                type="button"
                className="btn btn-primary"
                data-testid="expert-wizard-create"
                onClick={handleCreate}
                disabled={submitting}
              >
                {submitting ? 'Creating…' : 'Create Expert'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
