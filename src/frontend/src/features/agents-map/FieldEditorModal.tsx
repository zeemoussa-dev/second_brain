import type { ReactNode } from 'react';

// 2026-08-29 (operator: "we need to have a Big Pop up so we can fill
// the fields that needs a space to fill") -- generic modal shell for
// editing a single cramped side-panel field with real room. Same overlay/
// header/close convention as CreateAgentWizardModal.tsx's own
// .wizard-modal*, but a wider variant (.field-editor-modal) since the
// wizard's own 560px width is exactly the side panel's own width -- not
// "bigger" for this purpose. Content is fully controlled by the caller
// (a draft value + onChange passed into whatever picker/textarea renders
// as `children`); this shell only owns the chrome + Save/Cancel actions,
// matching every other field in this codebase's own draft-then-commit
// convention.
interface FieldEditorModalProps {
  title: string;
  description?: string;
  onClose: () => void;
  onSave: () => void;
  saving?: boolean;
  saveDisabled?: boolean;
  children: ReactNode;
}

export function FieldEditorModal({
  title,
  description,
  onClose,
  onSave,
  saving = false,
  saveDisabled = false,
  children,
}: FieldEditorModalProps) {
  return (
    <div className="field-editor-modal-overlay" data-testid="field-editor-modal-overlay" onClick={onClose}>
      <div
        className="field-editor-modal"
        data-testid="field-editor-modal"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="field-editor-modal-header">
          <h2>{title}</h2>
          <button
            type="button"
            className="field-editor-modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            &times;
          </button>
        </div>
        {description && <p className="field-editor-modal-description">{description}</p>}
        <div className="field-editor-modal-body">{children}</div>
        <div className="field-editor-modal-footer">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            disabled={saving || saveDisabled}
            onClick={onSave}
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
}
