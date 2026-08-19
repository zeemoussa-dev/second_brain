import { useEffect, useState } from 'react';
import { ApiError } from '../../api/client';
import { fetchSections, type SectionSummary } from '../settings/settingsApiClient';
import { createAgent, updateAgentAssignment, type AgentDetail } from './agentsApiClient';
import { fetchSkills, grantAgentSkill, type SkillSummary } from './skillsApiClient';
import { SkillsTree } from './SkillsTree';

type AgentType = 'worker' | 'expert' | 'producer';
type WorkingMode = 'autonomous' | 'supervised' | 'manual';
type Trigger = 'user' | 'agent' | 'schedule';

interface CreateAgentWizardModalProps {
  onClose: () => void;
  onCreated: (agent: AgentDetail) => void;
}

const WIZARD_STEP_IDS = [1, 2, 3, 4] as const;

export function CreateAgentWizardModal({ onClose, onCreated }: CreateAgentWizardModalProps) {
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);

  // Step 1 (REQ-SB-46-US-01-T02) — Name, Type, conditional Description
  // (Expert) / Scope (Worker), Section. ONE shared set of fields, not three
  // parallel per-type copies — lifted at this component level (not
  // step-local) since T03/T04/T05 all read these at final submit time.
  // Changing `type` only toggles which conditional field is visible; it
  // never clears `name`/`sectionId`/`domain`/`scopeDraft`.
  const [name, setName] = useState('');
  const [type, setType] = useState<AgentType>('expert');
  const [domain, setDomain] = useState('');
  const [scopeDraft, setScopeDraft] = useState('');
  const [sectionId, setSectionId] = useState('');
  const [step1Error, setStep1Error] = useState<string | null>(null);

  // Step 2 (REQ-SB-46-US-01-T03) — Working-mode selector (every Type) plus
  // Producer-only Purpose/output Skill.
  const [workingMode, setWorkingMode] = useState<WorkingMode>('autonomous');
  const [purposeDraft, setPurposeDraft] = useState('');
  const [selectedOutputSkillId, setSelectedOutputSkillId] = useState('');
  const [step2Error, setStep2Error] = useState<string | null>(null);

  // Step 3 (REQ-SB-46-US-01-T04) — shared SkillsTree.tsx, mode="select".
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [step3Error, setStep3Error] = useState<string | null>(null);

  // Step 4 (REQ-SB-46-US-01-T05) — summary + Trigger choice + submit.
  const [selectedTrigger, setSelectedTrigger] = useState<Trigger>('user');
  const [step4Error, setStep4Error] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [sections, setSections] = useState<SectionSummary[] | null>(null);
  // One shared Skill catalog fetch, reused by Step 2's Producer output-Skill
  // radio group AND Step 3's SkillsTree multi-select -- both read from the
  // same real /skills catalog, no divergent second fetch.
  const [skills, setSkills] = useState<SkillSummary[] | null>(null);

  useEffect(() => {
    fetchSections().then(setSections);
  }, []);

  useEffect(() => {
    fetchSkills().then(setSkills);
  }, []);

  function handleStep1Next() {
    const trimmedName = name.trim();
    const trimmedDomain = domain.trim();
    const missing: string[] = [];
    if (!trimmedName) missing.push('a name');
    if (!sectionId) missing.push('a Section');
    // Only Expert has a Step 1 conditional-field requirement -- Worker's
    // Scope and Producer's Purpose/output Skill are validated at their own
    // later steps (Step 3's Skills requirement; Step 4's final consistency
    // check), per this task's own explicit Step 1 "Next" validation scope.
    if (type === 'expert' && !trimmedDomain) missing.push('a knowledge domain');
    if (missing.length > 0) {
      setStep1Error(`Missing ${missing.join(', ')} — the agent was not created.`);
      return;
    }
    setStep1Error(null);
    setCurrentStep(2);
  }

  function handleStep2Next() {
    if (type === 'producer') {
      const missing: string[] = [];
      if (!purposeDraft.trim()) missing.push('a Purpose');
      if (!selectedOutputSkillId) missing.push('an output Skill');
      if (missing.length > 0) {
        setStep2Error(`Missing ${missing.join(', ')} — the agent was not created.`);
        return;
      }
    }
    setStep2Error(null);
    setCurrentStep(3);
  }

  function handleStep3Next() {
    if (type === 'worker' && selectedSkillIds.length === 0) {
      setStep3Error('Missing at least one Skill — the agent was not created.');
      return;
    }
    setStep3Error(null);
    setCurrentStep(4);
  }

  async function handleCreate() {
    // Defense-in-depth final consistency check (Scenario 10) -- each
    // step's own "Next" already gated this; the wizard's own navigation
    // cannot reach Step 4 with a missing field, so this never spuriously
    // blocks a genuinely complete submission.
    const trimmedName = name.trim();
    const trimmedDomain = domain.trim();
    const trimmedPurpose = purposeDraft.trim();
    const scope = scopeDraft
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    const missing: string[] = [];
    if (!trimmedName) missing.push('a name');
    if (!sectionId) missing.push('a Section');
    if (type === 'expert' && !trimmedDomain) missing.push('a knowledge domain');
    if (type === 'worker' && scope.length === 0) missing.push('a Vault Scope');
    if (type === 'worker' && selectedSkillIds.length === 0) missing.push('at least one Skill');
    if (type === 'producer' && !trimmedPurpose) missing.push('a Purpose');
    if (type === 'producer' && !selectedOutputSkillId) missing.push('an output Skill');
    if (missing.length > 0) {
      setStep4Error(`Missing ${missing.join(', ')} — the agent was not created.`);
      return;
    }
    setStep4Error(null);
    setSubmitting(true);
    try {
      let created: AgentDetail;
      let updated: AgentDetail;
      if (type === 'expert') {
        created = await createAgent({
          name: trimmedName,
          type: 'expert',
          domain: trimmedDomain,
          trigger: selectedTrigger,
        });
        // Skills at Step 3 are optional for Expert (Scenario 5) -- an empty
        // selection is a genuine no-op loop, keeping the call count/order
        // identical to today's shipped Expert flow (Scenario 7).
        for (const skillId of selectedSkillIds) {
          await grantAgentSkill(created.id, skillId);
        }
        updated = await updateAgentAssignment(created.id, {
          section_id: sectionId,
          working_mode: workingMode,
        });
      } else if (type === 'worker') {
        created = await createAgent({ name: trimmedName, type: 'worker', trigger: selectedTrigger });
        for (const skillId of selectedSkillIds) {
          await grantAgentSkill(created.id, skillId);
        }
        updated = await updateAgentAssignment(created.id, {
          section_id: sectionId,
          scope,
          working_mode: workingMode,
        });
      } else {
        created = await createAgent({
          name: trimmedName,
          type: 'producer',
          purpose: trimmedPurpose,
          trigger: selectedTrigger,
        });
        await grantAgentSkill(created.id, selectedOutputSkillId);
        // Step 3's own optional ADDITIONAL Skills, beyond the mandatory
        // output Skill already granted above -- never double-grant the
        // same id if it also happens to be selected in Step 3.
        for (const skillId of selectedSkillIds) {
          if (skillId !== selectedOutputSkillId) {
            await grantAgentSkill(created.id, skillId);
          }
        }
        updated = await updateAgentAssignment(created.id, {
          section_id: sectionId,
          working_mode: workingMode,
        });
      }
      onCreated(updated);
    } catch (err) {
      setStep4Error(
        err instanceof ApiError
          ? err.message
          : 'Something went wrong — the agent was not created.',
      );
    } finally {
      setSubmitting(false);
    }
  }

  const skillNameById = (skillId: string) => skills?.find((skill) => skill.id === skillId)?.name ?? skillId;
  const sectionNameById = (id: string) => sections?.find((section) => section.id === id)?.name ?? id;

  return (
    <div
      className="wizard-modal-overlay"
      data-testid="wizard-modal-overlay"
      onClick={onClose}
    >
      <div
        className="wizard-modal"
        data-testid="wizard-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="wizard-modal-header">
          <h2>Create agent</h2>
          <button
            type="button"
            className="wizard-modal-close"
            data-testid="wizard-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="wizard-step-bar" data-testid="wizard-step-bar">
          {WIZARD_STEP_IDS.map((stepNumber, index) => (
            <div className="wizard-step-item" key={stepNumber}>
              <div
                className={`wizard-step${stepNumber === currentStep ? ' wizard-step--current' : ''}`}
                data-testid={`wizard-step-${stepNumber}`}
                aria-current={stepNumber === currentStep ? 'step' : undefined}
              >
                {stepNumber}
              </div>
              {index < WIZARD_STEP_IDS.length - 1 && (
                <div className="wizard-step-connector" aria-hidden="true" />
              )}
            </div>
          ))}
        </div>
        <div className="wizard-modal-body">
          {currentStep === 1 && (
            <div data-testid="wizard-step1" className="item-row-actions">
              {step1Error && (
                <p className="text-muted" data-testid="wizard-step1-error">
                  <span className="badge badge-danger">Can't create agent</span> {step1Error}
                </p>
              )}
              <label className="text-muted" htmlFor="wizardStep1Name">Name</label>
              <input
                id="wizardStep1Name"
                className="input"
                data-testid="wizard-step1-name-input"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
              <label className="text-muted" htmlFor="wizardStep1Type">Type</label>
              <select
                id="wizardStep1Type"
                className="input"
                data-testid="wizard-step1-type-select"
                value={type}
                onChange={(event) => setType(event.target.value as AgentType)}
              >
                <option value="expert">Expert</option>
                <option value="worker">Worker</option>
                <option value="producer">Producer</option>
              </select>
              {type === 'expert' && (
                <>
                  <label className="text-muted" htmlFor="wizardStep1Description">Description</label>
                  <input
                    id="wizardStep1Description"
                    className="input"
                    data-testid="wizard-step1-description-input"
                    value={domain}
                    onChange={(event) => setDomain(event.target.value)}
                  />
                </>
              )}
              {type === 'worker' && (
                <>
                  <label className="text-muted" htmlFor="wizardStep1Scope">Vault scope</label>
                  <input
                    id="wizardStep1Scope"
                    type="text"
                    className="input"
                    data-testid="wizard-step1-scope-input"
                    value={scopeDraft}
                    onChange={(event) => setScopeDraft(event.target.value)}
                    placeholder="e.g. customer/masdar, Pipeline"
                  />
                </>
              )}
              <label className="text-muted" htmlFor="wizardStep1Section">Section</label>
              <select
                id="wizardStep1Section"
                className="input"
                data-testid="wizard-step1-section-select"
                value={sectionId}
                onChange={(event) => setSectionId(event.target.value)}
              >
                <option value="">Choose a Section…</option>
                {sections?.map((section) => (
                  <option key={section.id} value={section.id}>{section.name}</option>
                ))}
              </select>
              <button
                type="button"
                className="btn btn-primary"
                data-testid="wizard-step1-next"
                onClick={handleStep1Next}
              >
                Next
              </button>
            </div>
          )}
          {currentStep === 2 && (
            <div data-testid="wizard-step2" className="item-row-actions">
              {step2Error && (
                <p className="text-muted" data-testid="wizard-step2-error">
                  <span className="badge badge-danger">Can't create agent</span> {step2Error}
                </p>
              )}
              <label className="text-muted" htmlFor="wizardStep2WorkingMode">Working mode (Instructions/Guardrails)</label>
              <select
                id="wizardStep2WorkingMode"
                className="input"
                data-testid="wizard-step2-working-mode-select"
                value={workingMode}
                onChange={(event) => setWorkingMode(event.target.value as WorkingMode)}
              >
                <option value="autonomous">Autonomous</option>
                <option value="supervised">Supervised</option>
                <option value="manual">Manual</option>
              </select>
              {type === 'producer' && (
                <>
                  <label className="text-muted" htmlFor="wizardStep2Purpose">Purpose</label>
                  <textarea
                    id="wizardStep2Purpose"
                    className="input"
                    data-testid="wizard-step2-purpose-input"
                    value={purposeDraft}
                    onChange={(event) => setPurposeDraft(event.target.value)}
                  />
                  <span className="kv-key" data-testid="wizard-step2-output-skill-label">Output Skill</span>
                  <div data-testid="wizard-step2-output-skill-list">
                    {skills?.map((skill) => (
                      <label key={skill.id} className="text-muted">
                        <input
                          type="radio"
                          name="wizardStep2OutputSkill"
                          data-testid={`wizard-step2-output-skill-radio-${skill.id}`}
                          checked={selectedOutputSkillId === skill.id}
                          onChange={() => setSelectedOutputSkillId(skill.id)}
                        />
                        {skill.name}
                      </label>
                    ))}
                  </div>
                </>
              )}
              <div className="item-row-actions">
                <button type="button" className="btn" data-testid="wizard-step2-back" onClick={() => setCurrentStep(1)}>
                  Back
                </button>
                <button type="button" className="btn btn-primary" data-testid="wizard-step2-next" onClick={handleStep2Next}>
                  Next
                </button>
              </div>
            </div>
          )}
          {currentStep === 3 && (
            <div data-testid="wizard-step3" className="item-row-actions">
              {step3Error && (
                <p className="text-muted" data-testid="wizard-step3-error">
                  <span className="badge badge-danger">Can't create agent</span> {step3Error}
                </p>
              )}
              <div data-testid="wizard-step3-skills-tree">
                <SkillsTree
                  mode="select"
                  skills={(skills ?? []).map((skill) => ({
                    id: skill.id,
                    name: skill.name,
                    tool: skill.tool,
                    granted: false,
                  }))}
                  selectedIds={selectedSkillIds}
                  onChange={setSelectedSkillIds}
                />
              </div>
              <div className="item-row-actions">
                <button type="button" className="btn" data-testid="wizard-step3-back" onClick={() => setCurrentStep(2)}>
                  Back
                </button>
                <button type="button" className="btn btn-primary" data-testid="wizard-step3-next" onClick={handleStep3Next}>
                  Next
                </button>
              </div>
            </div>
          )}
          {currentStep === 4 && (
            <div data-testid="wizard-step4" className="item-row-actions">
              <div data-testid="wizard-step4-summary" className="kv-list">
                <div className="kv-row"><span className="kv-key">Name</span><span>{name}</span></div>
                <div className="kv-row"><span className="kv-key">Type</span><span>{type}</span></div>
                <div className="kv-row"><span className="kv-key">Section</span><span>{sectionNameById(sectionId)}</span></div>
                {type === 'expert' && (
                  <div className="kv-row"><span className="kv-key">Description</span><span>{domain}</span></div>
                )}
                {type === 'worker' && (
                  <div className="kv-row"><span className="kv-key">Vault scope</span><span>{scopeDraft}</span></div>
                )}
                <div className="kv-row"><span className="kv-key">Working mode</span><span>{workingMode}</span></div>
                {type === 'producer' && (
                  <>
                    <div className="kv-row"><span className="kv-key">Purpose</span><span>{purposeDraft}</span></div>
                    <div className="kv-row"><span className="kv-key">Output Skill</span><span>{skillNameById(selectedOutputSkillId)}</span></div>
                  </>
                )}
                <div className="kv-row">
                  <span className="kv-key">Skills</span>
                  <span>{selectedSkillIds.length > 0 ? selectedSkillIds.map(skillNameById).join(', ') : 'None'}</span>
                </div>
              </div>
              {step4Error && (
                <p className="text-muted" data-testid="wizard-step4-error">
                  <span className="badge badge-danger">Can't create agent</span> {step4Error}
                </p>
              )}
              <span className="kv-key">Trigger</span>
              <div className="item-row-actions">
                <label className="text-muted">
                  <input
                    type="radio"
                    name="wizardStep4Trigger"
                    data-testid="wizard-step4-trigger-user"
                    checked={selectedTrigger === 'user'}
                    onChange={() => setSelectedTrigger('user')}
                  />
                  User
                </label>
                <label className="text-muted">
                  <input
                    type="radio"
                    name="wizardStep4Trigger"
                    data-testid="wizard-step4-trigger-agent"
                    checked={selectedTrigger === 'agent'}
                    onChange={() => setSelectedTrigger('agent')}
                  />
                  Agent
                </label>
                <label className="text-muted">
                  <input
                    type="radio"
                    name="wizardStep4Trigger"
                    data-testid="wizard-step4-trigger-schedule"
                    checked={selectedTrigger === 'schedule'}
                    onChange={() => setSelectedTrigger('schedule')}
                  />
                  Schedule
                </label>
              </div>
              {selectedTrigger === 'schedule' && (
                <p className="text-muted" data-testid="wizard-step4-schedule-placeholder">
                  Schedule configuration happens on this agent's own Schedule tab, once it's available.
                </p>
              )}
              <div className="item-row-actions">
                <button type="button" className="btn" data-testid="wizard-step4-back" onClick={() => setCurrentStep(3)}>
                  Back
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  data-testid="wizard-step4-create"
                  onClick={handleCreate}
                  disabled={submitting}
                >
                  Create agent
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
