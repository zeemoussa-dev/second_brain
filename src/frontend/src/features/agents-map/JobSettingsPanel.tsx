import { useEffect, useState } from 'react';
import { fetchJobSettings, updateJobSettings, type JobSettings } from './agentsApiClient';

interface JobSettingsPanelProps {
  agentId: string;
  jobId: string;
  onClose: () => void;
}

// ADR-044 Decision 3 -- a genuinely separate, minimal Settings-only shell,
// never a widening of AgentDetailPanel.tsx's shared tab machinery (Option B
// rejected). Reuses the SAME side-panel/side-panel-overlay/kv-list/kv-row
// CSS classes AgentDetailPanel.tsx already uses -- no new visual language,
// per the parent story's own operator-directed "no /design pass" resolution
// -- but is its own component, not a code-shared subroutine.
export function JobSettingsPanel({ agentId, jobId, onClose }: JobSettingsPanelProps) {
  const [settings, setSettings] = useState<JobSettings | null>(null);
  const [promptDraft, setPromptDraft] = useState('');
  const [guardrailsDraft, setGuardrailsDraft] = useState('');

  useEffect(() => {
    setSettings(null); // clear stale content immediately on Job switch
    setPromptDraft('');
    setGuardrailsDraft('');
    fetchJobSettings(agentId, jobId).then((fetched) => {
      setSettings(fetched);
      setPromptDraft(fetched.prompt ?? '');
      setGuardrailsDraft(fetched.guardrails);
    });
  }, [agentId, jobId]);

  async function handlePromptCommit() {
    const updated = await updateJobSettings(agentId, jobId, { prompt: promptDraft });
    setSettings(updated);
    setPromptDraft(updated.prompt ?? '');
  }

  async function handleGuardrailsCommit() {
    const updated = await updateJobSettings(agentId, jobId, { guardrails: guardrailsDraft });
    setSettings(updated);
    setGuardrailsDraft(updated.guardrails);
  }

  // 'prompt' in settings keys off KEY PRESENCE, never an empty-string check
  // -- the backend genuinely OMITS the key for thread_match_merge/
  // detect_recurring_pattern (T06/ADR-044/AC-10), so an absent key must
  // never render the same empty-but-present row a real, unset override
  // would (an empty string IS a valid, present value for every other Job).
  const showPromptRow = settings !== null && 'prompt' in settings;

  return (
    <>
      <div className="side-panel-overlay" onClick={onClose} />
      <aside className="side-panel" aria-label="Job settings">
        <div className="side-panel-header">
          <span className="badge">Job settings</span>
          <button type="button" className="side-panel-close" aria-label="Close panel" onClick={onClose}>
            &times;
          </button>
        </div>
        {settings && (
          <div className="side-panel-title">
            <h2>{settings.name} <span className="badge">job</span></h2>
          </div>
        )}
        <div className="side-panel-body">
          {settings && (
            <div className="side-panel-section" data-testid="job-settings-panel">
              <h3>Settings</h3>
              <div className="kv-list">
                {showPromptRow && (
                  <div className="kv-row">
                    <span className="kv-key">Prompt</span>
                    <textarea
                      className="input kv-select"
                      style={{ minWidth: 220 }}
                      value={promptDraft}
                      onChange={(event) => setPromptDraft(event.target.value)}
                      onBlur={handlePromptCommit}
                      placeholder="No prompt override set — using the default"
                      data-testid="job-settings-prompt-input"
                    />
                  </div>
                )}
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
                    data-testid="job-settings-guardrails-input"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
