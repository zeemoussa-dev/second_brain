// The "+" FAB's own type-select menu (operator, 2026-08-30: "The Plus
// Should show a context menu (Bueatiful one to create Expert, Producer,
// Worker, Pipeline and Section)"). Only Expert has a real creation flow
// behind it right now; the other four are deliberately visible but
// disabled, "not implemented still coming soon" per the operator's own
// scoping -- a real menu with real future options, not a placeholder
// that has to be rebuilt from scratch once those flows exist.
export type AgentTypeMenuChoice = 'expert' | 'producer' | 'worker' | 'pipeline' | 'section';

interface AgentTypeMenuOption {
  id: AgentTypeMenuChoice;
  label: string;
  description: string;
  icon: string;
  enabled: boolean;
}

const AGENT_TYPE_MENU_OPTIONS: AgentTypeMenuOption[] = [
  { id: 'expert', label: 'Expert', description: 'A knowledge specialist agents and people can consult', icon: 'psychology', enabled: true },
  { id: 'producer', label: 'Producer', description: 'Writes new notes/results into the vault', icon: 'conveyor_belt', enabled: false },
  { id: 'worker', label: 'Worker', description: 'One step inside a larger Pipeline', icon: 'build', enabled: false },
  { id: 'pipeline', label: 'Pipeline', description: 'A scheduled chain of Worker/Producer steps', icon: 'route', enabled: false },
  { id: 'section', label: 'Section', description: 'A new Hub grouping on the map', icon: 'dashboard', enabled: false },
];

interface AgentTypeMenuProps {
  onClose: () => void;
  onSelect: (choice: AgentTypeMenuChoice) => void;
}

export function AgentTypeMenu({ onClose, onSelect }: AgentTypeMenuProps) {
  return (
    <div className="agent-type-menu-overlay" data-testid="agent-type-menu-overlay" onClick={onClose}>
      <div
        className="agent-type-menu"
        data-testid="agent-type-menu"
        role="menu"
        onClick={(event) => event.stopPropagation()}
      >
        <p className="agent-type-menu-title">Create</p>
        {AGENT_TYPE_MENU_OPTIONS.map((option) => (
          <button
            key={option.id}
            type="button"
            role="menuitem"
            className="agent-type-menu-item"
            data-testid={`agent-type-menu-item-${option.id}`}
            disabled={!option.enabled}
            onClick={() => option.enabled && onSelect(option.id)}
          >
            <span className="agent-type-menu-item-icon material-symbols-outlined" aria-hidden="true">
              {option.icon}
            </span>
            <span className="agent-type-menu-item-text">
              <span className="agent-type-menu-item-label">{option.label}</span>
              <span className="agent-type-menu-item-desc">{option.description}</span>
            </span>
            {!option.enabled && <span className="badge agent-type-menu-item-badge">Coming soon</span>}
          </button>
        ))}
      </div>
    </div>
  );
}
