import type { ReactNode } from 'react';

// A plain placeholder disappears the moment a field has a value, so a
// filled-in row gives no clue which field is which (operator: "When you
// add the text I don't have a title for the textbox so i don't know what
// that is"). Every Settings field gets a real, persistent label instead.
// Shared across Settings pages (Vault > Entities, Sections, ...).
export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="field-labeled">
      <span className="field-labeled-label">{label}</span>
      {children}
    </label>
  );
}
