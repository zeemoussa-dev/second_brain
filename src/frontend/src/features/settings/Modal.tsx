import type { ReactNode } from 'react';

// Generic popup shell (operator, 2026-09-01: "The Confirmation should be
// a popup not in the header of the Page") -- same overlay/header/close
// chrome convention as FieldEditorModal.tsx/CreateExpertWizardModal.tsx,
// but with a fully caller-controlled footer (children, not a fixed
// Save/Cancel pair) since the Export/Import flows this backs each render
// a different action set per internal step.
interface ModalProps {
  title: string;
  description?: string;
  onClose: () => void;
  footer?: ReactNode;
  children: ReactNode;
}

export function Modal({ title, description, onClose, footer, children }: ModalProps) {
  return (
    <div className="settings-modal-overlay" data-testid="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" data-testid="settings-modal" onClick={(event) => event.stopPropagation()}>
        <div className="settings-modal-header">
          <h2>{title}</h2>
          <button type="button" className="settings-modal-close" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>
        {description && <p className="settings-modal-description">{description}</p>}
        <div className="settings-modal-body">{children}</div>
        {footer && <div className="settings-modal-footer">{footer}</div>}
      </div>
    </div>
  );
}
