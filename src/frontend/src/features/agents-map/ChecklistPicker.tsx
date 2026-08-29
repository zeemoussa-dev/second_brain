// Generic checkbox list for a FieldEditorModal's content -- reused by
// every list-shaped field whose real options are a flat catalog (Tools'
// real toolset catalog, Relays-to's real agent list, Preferred indexes'
// real Index list, and the flat-folder half of a Vault Scope / Section
// Folders picker). Fully controlled: no internal state, the caller owns
// the selected set and the Save action.
export interface ChecklistItem {
  id: string;
  label: string;
  meta?: string;
}

interface ChecklistPickerProps {
  items: ChecklistItem[];
  selectedIds: string[];
  onToggle: (id: string) => void;
  emptyLabel?: string;
}

export function ChecklistPicker({ items, selectedIds, onToggle, emptyLabel = 'Nothing available yet.' }: ChecklistPickerProps) {
  if (items.length === 0) {
    return <p className="text-muted">{emptyLabel}</p>;
  }
  return (
    <div className="checklist-picker" data-testid="checklist-picker">
      {items.map((item) => (
        <label className="checklist-picker-row" key={item.id}>
          <input
            type="checkbox"
            checked={selectedIds.includes(item.id)}
            onChange={() => onToggle(item.id)}
          />
          <span className="checklist-picker-label">{item.label}</span>
          {item.meta && <span className="checklist-picker-meta">{item.meta}</span>}
        </label>
      ))}
    </div>
  );
}
