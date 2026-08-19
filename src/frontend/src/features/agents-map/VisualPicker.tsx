import { VISUAL_COLORS, VISUAL_ICONS } from './visualOptions';

interface VisualPickerProps {
  selectedIcon: string | null;
  selectedColor: string | null;
  onSelectIcon: (iconId: string) => void;
  onSelectColor: (colorHex: string) => void;
  onReset: () => void;
}

// Shared icon+color picker — reused by the Agent detail panel's Visual
// tab and (once Hubs get their own settings surface) Section Hubs, one
// component instead of the 6 hand-duplicated prototype copies.
export function VisualPicker({ selectedIcon, selectedColor, onSelectIcon, onSelectColor, onReset }: VisualPickerProps) {
  return (
    <div className="visual-picker" data-testid="visual-picker">
      <p className="visual-picker-hint">Icon</p>
      <div className="visual-picker-icon-grid" role="group" aria-label="Icon">
        {VISUAL_ICONS.map((icon) => (
          <button
            key={icon.id}
            type="button"
            className={`visual-picker-icon${selectedIcon === icon.id ? ' visual-picker-icon--selected' : ''}`}
            aria-pressed={selectedIcon === icon.id}
            aria-label={icon.label}
            title={icon.label}
            onClick={() => onSelectIcon(icon.id)}
          >
            <span className="material-symbols-outlined" aria-hidden="true">{icon.icon}</span>
          </button>
        ))}
      </div>
      <p className="visual-picker-hint">Color</p>
      <div className="visual-picker-color-row" role="group" aria-label="Color">
        {VISUAL_COLORS.map((color) => (
          <button
            key={color}
            type="button"
            className={`visual-picker-color${selectedColor === color ? ' visual-picker-color--selected' : ''}`}
            aria-pressed={selectedColor === color}
            aria-label={color}
            title={color}
            style={{ backgroundColor: color }}
            onClick={() => onSelectColor(color)}
          />
        ))}
      </div>
      <button type="button" className="btn visual-picker-reset" onClick={onReset}>
        Reset to default
      </button>
    </div>
  );
}
