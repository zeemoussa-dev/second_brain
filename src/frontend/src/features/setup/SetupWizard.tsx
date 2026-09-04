import { useEffect, useState } from 'react';
import type { CheckResult, HermesHealth, SaveResult, SetupField, SetupStatus } from './setupApiClient';
import {
  getHermesHealth,
  getSetupStatus,
  restartBackend,
  saveSetup,
  testCompass,
  validateField,
} from './setupApiClient';

/** REQ-SB-89 -- the first-run setup wizard.
 *
 * Replaces hand-editing .env on a fresh install. Two entry points, one
 * component: BootGate renders it automatically when the backend reports
 * setup_required, and /setup renders it on demand so it can be re-run
 * deliberately without deleting .env first (operator's own choice).
 *
 * Every value is checked against the REAL machine before the operator can
 * move on -- a folder that doesn't exist, a Compass URL missing its
 * endpoint, credentials that don't actually authenticate. The whole point
 * is to fail here, where the fix is one keystroke away, instead of at first
 * use hours later. */

const HERMES_STEP_ID = 'hermes';

function CheckBadge({ result, pending }: { result?: CheckResult; pending?: boolean }) {
  if (pending) return <span className="setup-check setup-check-pending">Checking…</span>;
  if (!result) return null;
  return (
    <span className={`setup-check ${result.ok ? 'setup-check-ok' : 'setup-check-bad'}`}>
      <span className="material-symbols-outlined setup-check-icon">
        {result.ok ? 'check_circle' : 'error'}
      </span>
      {result.detail}
    </span>
  );
}

function FieldRow({
  field,
  value,
  result,
  pending,
  onChange,
  onBlur,
}: {
  field: SetupField;
  value: string;
  result?: CheckResult;
  pending?: boolean;
  onChange: (value: string) => void;
  onBlur: () => void;
}) {
  return (
    <div className="setup-field">
      <label className="setup-field-label" htmlFor={`setup-${field.key}`}>
        <span className="material-symbols-outlined setup-field-icon">{field.icon}</span>
        {field.label}
        {field.required && <span className="setup-field-required">required</span>}
      </label>
      <p className="setup-field-description">{field.description}</p>
      <input
        id={`setup-${field.key}`}
        className="setup-field-input"
        type={field.secret ? 'password' : 'text'}
        value={value}
        spellCheck={false}
        autoComplete="off"
        onChange={(event) => onChange(event.target.value)}
        onBlur={onBlur}
      />
      <CheckBadge result={result} pending={pending} />
    </div>
  );
}

function HermesHealthPanel({ health, loading }: { health: HermesHealth | null; loading: boolean }) {
  if (loading) return <p className="setup-hermes-loading">Looking at your Hermes install…</p>;
  if (!health) return null;
  return (
    <div className="setup-hermes">
      <ul className="setup-hermes-list">
        {health.checks.map((check) => (
          <li key={check.key} className={`setup-hermes-row ${check.ok ? 'is-ok' : 'is-bad'}`}>
            <span className="material-symbols-outlined setup-hermes-icon">
              {check.ok ? 'check_circle' : 'error'}
            </span>
            <span className="setup-hermes-label">{check.label}</span>
            <span className="setup-hermes-detail">{check.detail}</span>
          </li>
        ))}
      </ul>
      {/* Precise about the one thing that IS written, so nothing about the
          Hermes side comes as a surprise after saving. */}
      <p className="setup-hermes-note">
        Saving writes four settings into Hermes' own <code>.env</code> — your vault path (as both{' '}
        <code>OBSIDIAN_VAULT_PATH</code> and <code>SECOND_BRAIN_VAULT_PATH</code>),{' '}
        <code>SECOND_BRAIN_DATA_PATH</code> and <code>SECOND_BRAIN_SELF_EMAIL</code> — into the home
        file and every profile, because Hermes gives each profile its own environment and never
        falls back to the top-level one. That's the only change the wizard makes here. Everything
        else above is read-only: profiles, skills, and scheduled jobs stay yours to manage with the
        Hermes CLI.
      </p>
    </div>
  );
}

export function SetupWizard({ onDismiss }: { onDismiss?: () => void }) {
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [values, setValues] = useState<Record<string, string>>({});
  const [checks, setChecks] = useState<Record<string, CheckResult>>({});
  const [checking, setChecking] = useState<Record<string, boolean>>({});
  const [compassResult, setCompassResult] = useState<CheckResult | null>(null);
  const [testingCompass, setTestingCompass] = useState(false);
  const [hermesHealth, setHermesHealth] = useState<HermesHealth | null>(null);
  const [hermesLoading, setHermesLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState<SaveResult | null>(null);
  const [advancing, setAdvancing] = useState(false);

  useEffect(() => {
    getSetupStatus()
      .then((next) => {
        setStatus(next);
        const seeded: Record<string, string> = {};
        for (const step of next.steps) {
          for (const field of step.fields) seeded[field.key] = field.value;
        }
        setValues(seeded);
      })
      .catch(() => setStatus(null));
  }, []);

  const step = status?.steps[stepIndex];

  const vaultPathValue = values.vault_path ?? '';

  useEffect(() => {
    if (step?.id !== HERMES_STEP_ID) return;
    setHermesLoading(true);
    getHermesHealth(vaultPathValue)
      .then(setHermesHealth)
      .catch(() => setHermesHealth(null))
      .finally(() => setHermesLoading(false));
  }, [step?.id, vaultPathValue]);

  if (!status) {
    return (
      <div className="setup-screen">
        <div className="setup-panel">
          <p className="setup-eyebrow">Second Brain</p>
          <h1 className="setup-title">Setup</h1>
          <p className="setup-blurb">Connecting to the backend…</p>
        </div>
      </div>
    );
  }

  async function runCheck(field: SetupField, value: string) {
    // A secret left at its mask hasn't been touched, so there is nothing
    // meaningful to check and a "looks fine" badge would be a lie.
    if (field.secret && value === values[field.key] && !value.trim()) return;
    setChecking((prev) => ({ ...prev, [field.key]: true }));
    try {
      const result = await validateField(field.key, value);
      setChecks((prev) => ({ ...prev, [field.key]: result }));
    } catch {
      setChecks((prev) => ({
        ...prev,
        [field.key]: { ok: false, detail: "Couldn't check that right now" },
      }));
    } finally {
      setChecking((prev) => ({ ...prev, [field.key]: false }));
    }
  }

  /** Re-checks every field on this step and only advances if all pass.
   *  onBlur alone isn't enough: its check is async, so clicking Next fires
   *  before the result lands and a bad path would sail through unvalidated.
   *  Re-running here is cheap and makes "Next" mean "this step is really
   *  right", not "nothing had come back yet". */
  async function handleNext() {
    if (!step) return;
    setAdvancing(true);
    try {
      const results = await Promise.all(
        step.fields.map(async (field) => {
          const value = values[field.key] ?? '';
          if (!field.required && !value.trim()) return { key: field.key, result: null };
          try {
            return { key: field.key, result: await validateField(field.key, value) };
          } catch {
            return { key: field.key, result: { ok: false, detail: "Couldn't check that right now" } };
          }
        }),
      );
      const settled: Record<string, CheckResult> = {};
      for (const { key, result } of results) if (result) settled[key] = result;
      setChecks((prev) => ({ ...prev, ...settled }));
      if (Object.values(settled).every((result) => result.ok)) {
        setStepIndex((index) => index + 1);
      }
    } finally {
      setAdvancing(false);
    }
  }

  async function handleTestCompass() {
    setTestingCompass(true);
    try {
      setCompassResult(await testCompass(values));
    } catch {
      setCompassResult({ ok: false, detail: "Couldn't reach Compass to test it" });
    } finally {
      setTestingCompass(false);
    }
  }

  async function handleFinish() {
    setSaving(true);
    setSaveError(null);
    try {
      // Everything, not just this step: the operator may have edited an
      // earlier step and come back without re-blurring the field.
      const allFields = (status?.steps ?? []).flatMap((candidate) => candidate.fields);
      const results = await Promise.all(
        allFields
          .filter((field) => field.required || (values[field.key] ?? '').trim())
          .map(async (field) => ({
            field,
            result: await validateField(field.key, values[field.key] ?? '').catch(() => ({
              ok: false,
              detail: "Couldn't check that right now",
            })),
          })),
      );
      setChecks((prev) => ({
        ...prev,
        ...Object.fromEntries(results.map(({ field, result }) => [field.key, result])),
      }));
      const bad = results.filter(({ result }) => !result.ok);
      if (bad.length > 0) {
        setSaveError(
          `Not saved — fix these first: ${bad.map(({ field }) => field.label).join(', ')}`,
        );
        return;
      }
      setSaved(await saveSetup(values));
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Saving failed');
    } finally {
      setSaving(false);
    }
  }

  async function handleRestart() {
    try {
      await restartBackend();
    } catch {
      // The backend going away mid-request IS the success case here -- the
      // shutdown it just accepted is what kills the response. Treat a
      // failed fetch as done, not as an error worth alarming about.
    }
  }

  if (saved) {
    return (
      <div className="setup-screen">
        <div className="setup-panel">
          <p className="setup-eyebrow">Second Brain</p>
          <h1 className="setup-title">Saved</h1>
          <p className="setup-blurb">
            Your settings are written to <code>.env</code>. Second Brain reads them once at startup,
            so it needs a restart to pick them up.
          </p>
          {/* Stated outright, pass or fail: this is the one thing the wizard
              changes outside its own .env, so it should never be a silent
              side effect of pressing Save. */}
          <p className={`setup-check ${saved.hermes_vault_sync.ok ? 'setup-check-ok' : 'setup-check-bad'}`}>
            <span className="material-symbols-outlined setup-check-icon">
              {saved.hermes_vault_sync.ok ? 'check_circle' : 'error'}
            </span>
            {saved.hermes_vault_sync.detail}
          </p>
          {saved.hermes_vault_sync.ok && (
            <p className="setup-hint">
              Hermes won't re-read its <code>.env</code> while it's running — restart Hermes too, or
              its agents keep using the old vault path.
            </p>
          )}
          <div className="setup-actions">
            <button type="button" className="setup-button setup-button-primary" onClick={handleRestart}>
              Restart now
            </button>
            {onDismiss && (
              <button type="button" className="setup-button" onClick={onDismiss}>
                Later
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  const isLastStep = stepIndex === status.steps.length - 1;
  // Only fields this step is actually responsible for can block it. A
  // required field already carrying a real value (a re-run, or a secret
  // showing its mask) counts as answered.
  const blocking = (step?.fields ?? []).filter(
    (field) => field.required && !(values[field.key] ?? '').trim(),
  );
  const failed = (step?.fields ?? []).filter((field) => checks[field.key]?.ok === false);
  const canAdvance = blocking.length === 0 && failed.length === 0;

  return (
    <div className="setup-screen">
      <div className="setup-panel setup-panel-wide">
        <p className="setup-eyebrow">Second Brain</p>
        <h1 className="setup-title">Set up Second Brain</h1>
        <p className="setup-blurb">
          A few things Second Brain needs before it can read your vault. Each one is checked against
          this machine as you go.
        </p>

        <ol className="setup-steps">
          {status.steps.map((candidate, index) => (
            <li
              key={candidate.id}
              className={`setup-step-pip ${index === stepIndex ? 'is-current' : ''} ${index < stepIndex ? 'is-done' : ''}`}
            >
              {candidate.title}
            </li>
          ))}
        </ol>

        {step && (
          <div className="setup-step">
            <h2 className="setup-step-title">{step.title}</h2>
            <p className="setup-step-blurb">{step.blurb}</p>

            {step.fields.map((field) => (
              <FieldRow
                key={field.key}
                field={field}
                value={values[field.key] ?? ''}
                result={checks[field.key]}
                pending={checking[field.key]}
                onChange={(value) => setValues((prev) => ({ ...prev, [field.key]: value }))}
                onBlur={() => runCheck(field, values[field.key] ?? '')}
              />
            ))}

            {step.id === 'compass' && (
              <div className="setup-inline-test">
                <button
                  type="button"
                  className="setup-button"
                  onClick={handleTestCompass}
                  disabled={testingCompass}
                >
                  {testingCompass ? 'Testing…' : 'Test connection'}
                </button>
                <CheckBadge result={compassResult ?? undefined} />
                <p className="setup-inline-test-note">
                  The only check that proves the URL, key, and model work together.
                </p>
              </div>
            )}

            {step.id === HERMES_STEP_ID && (
              <HermesHealthPanel health={hermesHealth} loading={hermesLoading} />
            )}
          </div>
        )}

        {saveError && <p className="setup-error">{saveError}</p>}

        <div className="setup-actions">
          <button
            type="button"
            className="setup-button"
            onClick={() => setStepIndex((index) => Math.max(0, index - 1))}
            disabled={stepIndex === 0}
          >
            Back
          </button>
          {isLastStep ? (
            <button
              type="button"
              className="setup-button setup-button-primary"
              onClick={handleFinish}
              disabled={saving || !canAdvance}
            >
              {saving ? 'Saving…' : 'Save and finish'}
            </button>
          ) : (
            <button
              type="button"
              className="setup-button setup-button-primary"
              onClick={handleNext}
              disabled={!canAdvance || advancing}
            >
              {advancing ? 'Checking…' : 'Next'}
            </button>
          )}
          {onDismiss && (
            <button type="button" className="setup-button setup-button-quiet" onClick={onDismiss}>
              Cancel
            </button>
          )}
        </div>

        {!canAdvance && (
          <p className="setup-hint">
            {blocking.length > 0
              ? `Still needed: ${blocking.map((field) => field.label).join(', ')}`
              : `Fix before continuing: ${failed.map((field) => field.label).join(', ')}`}
          </p>
        )}
      </div>
    </div>
  );
}
