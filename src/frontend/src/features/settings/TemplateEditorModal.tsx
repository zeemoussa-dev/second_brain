import { useEffect, useState } from 'react';
import { Modal } from './Modal';
import { extractErrorDetail } from './artifactFlowUtils';
import { fetchTemplateJson, saveTemplateJson } from './vaultApiClient';

// Shows one Template's JSON and lets the operator edit it (2026-09-22). The
// server validates before writing, so a Template the framework cannot use is
// refused with the reason and nothing on disk changes.

interface TemplateEditorModalProps {
  templateId: string;
  onClose: () => void;
}

function format(json: unknown): string {
  return JSON.stringify(json, null, 2);
}

export function TemplateEditorModal({ templateId, onClose }: TemplateEditorModalProps) {
  const [saved, setSaved] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [editing, setEditing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    fetchTemplateJson(templateId)
      .then((result) => {
        setSaved(format(result.json));
        setDraft(format(result.json));
      })
      .catch((e) => setError(extractErrorDetail(e)));
  }, [templateId]);

  const dirty = editing && saved !== null && draft !== saved;

  function versionOf(text: string | null): unknown {
    try {
      return text === null ? undefined : (JSON.parse(text) as { version?: unknown }).version;
    } catch {
      return undefined;
    }
  }

  function close() {
    if (dirty && !window.confirm('Discard your changes to this Template?')) {
      return;
    }
    onClose();
  }

  async function save() {
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(draft) as Record<string, unknown>;
    } catch (e) {
      setError(`Not valid JSON: ${(e as Error).message}`);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const versionChanged = versionOf(saved) !== parsed.version;
      const result = await saveTemplateJson(templateId, parsed);
      setSaved(format(result.json));
      setDraft(format(result.json));
      setEditing(false);
      setNotice(
        versionChanged
          ? 'Saved. The version changed: Skills that write this Template declare the version they expect, '
            + 'so update their writes: and redeploy them, or deploying will refuse.'
          : 'Saved. It takes effect on the next capture run.',
      );
    } catch (e) {
      setError(extractErrorDetail(e));
    } finally {
      setBusy(false);
    }
  }

  const footer = editing ? (
    <>
      <button
        type="button"
        className="btn"
        disabled={busy}
        onClick={() => {
          setDraft(saved ?? '');
          setEditing(false);
          setError(null);
        }}
      >
        Cancel
      </button>
      <button type="button" className="btn btn-primary" data-testid="template-save" disabled={busy || !dirty} onClick={save}>
        {busy ? 'Saving…' : 'Save'}
      </button>
    </>
  ) : (
    <>
      <button type="button" className="btn" onClick={close}>Close</button>
      <button
        type="button"
        className="btn btn-primary"
        data-testid="template-edit"
        disabled={saved === null}
        onClick={() => {
          setEditing(true);
          setNotice(null);
        }}
      >
        Edit
      </button>
    </>
  );

  return (
    <Modal
      title={`Template: ${templateId}`}
      description={
        editing
          ? 'Edits reach the vault on the next capture run. The id cannot change here, and a Template the '
            + 'framework cannot read is refused with the reason.'
          : 'The Template.json on this install, exactly as it is.'
      }
      onClose={close}
      footer={footer}
    >
      {error && (
        <p data-role="template-error" style={{ color: 'var(--color-danger)', marginTop: 0 }}>{error}</p>
      )}
      {notice && <p data-role="template-notice" className="text-muted" style={{ marginTop: 0 }}>{notice}</p>}
      {saved === null && !error && <p className="text-muted">Loading...</p>}
      {saved !== null && (editing ? (
        <textarea
          className="template-json template-json--editing"
          data-testid="template-json-editor"
          value={draft}
          spellCheck={false}
          onChange={(event) => setDraft(event.target.value)}
        />
      ) : (
        <pre className="template-json" data-testid="template-json-view">{saved}</pre>
      ))}
    </Modal>
  );
}
