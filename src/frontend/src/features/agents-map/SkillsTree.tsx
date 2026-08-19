import { useState } from 'react';

// Standalone, mode-parameterized Tool-grouped Skills tree (REQ-SB-48-US-01-T02).
// `mode="manage"` (this task's own scope) is AgentDetailPanel's Capabilities
// section: collapsible Tool groups, a fixed icon per Tool, and a multi-select
// bulk Grant/Revoke action composed from N sequential single-Skill calls, on
// top of the existing single-row Grant/Revoke buttons (unchanged mechanism).
//
// `mode="select"` is a real, already-wired cross-story dependency, NOT this
// task's own scope to fully design: REQ-SB-46-US-01-T04 (Agent Creation
// Wizard Step 3 Skills picker, SPRINT-043, ADR-039 point 2) reuses this
// SAME component/file for a pure, controlled multi-select with no grant/
// revoke API call. Built here as a minimal, literal implementation of what
// that task's own prose already specifies (checkboxes + selectedIds/onChange,
// no API call) so this file is genuinely standalone/importable/extractable
// today -- T04 owns wiring it into the wizard's own state and may still
// refine this branch's own selection semantics (e.g. cross-group behaviour)
// for its own story's needs; nothing here should be read as that story's
// final answer.

export const SKILLS_TREE_TOOL_ORDER = ['Outlook', 'Vault', 'Web', 'Compass'] as const;
export type SkillsTreeToolName = (typeof SKILLS_TREE_TOOL_ORDER)[number];

// Fixed icon per Tool (Sidebar.tsx's own .nav-icon Unicode-glyph convention,
// REQ-SB-48-US-01's Constraints) -- inherited by every Skill row under that
// Tool, never a distinct icon per individual Skill.
const SKILLS_TREE_TOOL_ICONS: Record<SkillsTreeToolName, string> = {
  Outlook: '✉',
  Vault: '🗄',
  Web: '🌐',
  Compass: '🧭',
};

export interface SkillsTreeSkill {
  id: string;
  name: string;
  tool: string;
  /** Manage mode only — whether the agent currently holds this skill. */
  granted: boolean;
}

interface SkillsTreeManageProps {
  mode: 'manage';
  skills: SkillsTreeSkill[];
  /** Per-row single-Skill grant/revoke — the exact existing one-at-a-time
   * mechanism the flat Capabilities list already used before this tree
   * (Scenario 8's own "unchanged by this task" mechanism). */
  onGrantSkill: (skillId: string) => void;
  onRevokeSkill: (skillId: string) => void;
  /** Multi-select bulk actions — the caller composes N sequential calls to
   * the same single-Skill grant/revoke primitive above; SkillsTree itself
   * never calls a batch endpoint (Scenarios 5/6). */
  onGrantSkills: (skillIds: string[]) => void;
  onRevokeSkills: (skillIds: string[]) => void;
}

interface SkillsTreeSelectProps {
  mode: 'select';
  skills: SkillsTreeSkill[];
  selectedIds: string[];
  onChange: (selectedIds: string[]) => void;
}

export type SkillsTreeProps = SkillsTreeManageProps | SkillsTreeSelectProps;

function useSkillsTreeCollapse() {
  const [collapsedTools, setCollapsedTools] = useState<Set<string>>(new Set());
  function toggleCollapse(tool: string, onCollapsed?: (tool: string) => void) {
    setCollapsedTools((prev) => {
      const next = new Set(prev);
      if (next.has(tool)) {
        next.delete(tool);
      } else {
        next.add(tool);
        onCollapsed?.(tool);
      }
      return next;
    });
  }
  return { collapsedTools, toggleCollapse };
}

function ToolGroupHeader({ tool, icon, collapsed, onToggle }: {
  tool: string;
  icon: string;
  collapsed: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      className="skills-tree-group-header"
      onClick={onToggle}
      aria-expanded={!collapsed}
      data-testid={`skills-tree-toggle-${tool}`}
    >
      <span className="skills-tree-icon" aria-hidden="true">{icon}</span>
      <span className="skills-tree-group-name">{tool}</span>
      <span className="skills-tree-collapse-indicator" aria-hidden="true">{collapsed ? '▸' : '▾'}</span>
    </button>
  );
}

interface ManageSelection {
  tool: string;
  granted: boolean;
  ids: Set<string>;
}

function SkillsTreeManageView({ skills, onGrantSkill, onRevokeSkill, onGrantSkills, onRevokeSkills }: SkillsTreeManageProps) {
  const { collapsedTools, toggleCollapse } = useSkillsTreeCollapse();
  const [selection, setSelection] = useState<ManageSelection | null>(null);

  function toggleSelect(tool: string, skillId: string, granted: boolean) {
    setSelection((prev) => {
      if (!prev || prev.tool !== tool || prev.granted !== granted) {
        return { tool, granted, ids: new Set([skillId]) };
      }
      const ids = new Set(prev.ids);
      if (ids.has(skillId)) {
        ids.delete(skillId);
      } else {
        ids.add(skillId);
      }
      return ids.size > 0 ? { tool, granted, ids } : null;
    });
  }

  function handleBulkAction() {
    if (!selection) return;
    const ids = Array.from(selection.ids);
    if (selection.granted) {
      onRevokeSkills(ids);
    } else {
      onGrantSkills(ids);
    }
    setSelection(null);
  }

  return (
    <div className="skills-tree" data-testid="skills-tree">
      {SKILLS_TREE_TOOL_ORDER.map((tool) => {
        const toolSkills = skills.filter((skill) => skill.tool === tool);
        const collapsed = collapsedTools.has(tool);
        const icon = SKILLS_TREE_TOOL_ICONS[tool];
        return (
          <div className="skills-tree-group" key={tool} data-testid={`skills-tree-group-${tool}`}>
            <ToolGroupHeader
              tool={tool}
              icon={icon}
              collapsed={collapsed}
              onToggle={() =>
                toggleCollapse(tool, (collapsedTool) =>
                  setSelection((current) => (current && current.tool === collapsedTool ? null : current)),
                )
              }
            />
            {!collapsed && (
              <div className="skills-tree-rows" data-testid={`skills-tree-rows-${tool}`}>
                {toolSkills.map((skill) => (
                  <div
                    className="skills-tree-row kv-row"
                    key={skill.id}
                    data-testid={`skills-tree-row-${skill.id}`}
                    data-granted={skill.granted}
                  >
                    <input
                      type="checkbox"
                      className="skills-tree-checkbox"
                      checked={selection?.tool === tool && selection.ids.has(skill.id)}
                      onChange={() => toggleSelect(tool, skill.id, skill.granted)}
                      aria-label={`Select ${skill.name}`}
                    />
                    <span className="skills-tree-icon" aria-hidden="true">{icon}</span>
                    <span className="kv-key">{skill.name}</span>
                    {skill.granted ? (
                      <button type="button" className="btn btn-danger" onClick={() => onRevokeSkill(skill.id)}>
                        Revoke
                      </button>
                    ) : (
                      <button type="button" className="btn btn-primary" onClick={() => onGrantSkill(skill.id)}>
                        Grant
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
      {selection && (
        <div className="skills-tree-bulk-actions" data-testid="skills-tree-bulk-actions">
          <span className="text-muted">{selection.ids.size} selected</span>
          <button
            type="button"
            className={selection.granted ? 'btn btn-danger' : 'btn btn-primary'}
            onClick={handleBulkAction}
            data-testid="skills-tree-bulk-action-button"
          >
            {selection.granted ? `Revoke (${selection.ids.size})` : `Grant (${selection.ids.size})`}
          </button>
        </div>
      )}
    </div>
  );
}

function SkillsTreeSelectView({ skills, selectedIds, onChange }: SkillsTreeSelectProps) {
  const { collapsedTools, toggleCollapse } = useSkillsTreeCollapse();

  function toggle(skillId: string) {
    const next = selectedIds.includes(skillId)
      ? selectedIds.filter((id) => id !== skillId)
      : [...selectedIds, skillId];
    onChange(next);
  }

  return (
    <div className="skills-tree" data-testid="skills-tree">
      {SKILLS_TREE_TOOL_ORDER.map((tool) => {
        const toolSkills = skills.filter((skill) => skill.tool === tool);
        const collapsed = collapsedTools.has(tool);
        const icon = SKILLS_TREE_TOOL_ICONS[tool];
        return (
          <div className="skills-tree-group" key={tool} data-testid={`skills-tree-group-${tool}`}>
            <ToolGroupHeader tool={tool} icon={icon} collapsed={collapsed} onToggle={() => toggleCollapse(tool)} />
            {!collapsed && (
              <div className="skills-tree-rows" data-testid={`skills-tree-rows-${tool}`}>
                {toolSkills.map((skill) => (
                  <div className="skills-tree-row kv-row" key={skill.id} data-testid={`skills-tree-row-${skill.id}`}>
                    <input
                      type="checkbox"
                      className="skills-tree-checkbox"
                      checked={selectedIds.includes(skill.id)}
                      onChange={() => toggle(skill.id)}
                      aria-label={`Select ${skill.name}`}
                    />
                    <span className="skills-tree-icon" aria-hidden="true">{icon}</span>
                    <span className="kv-key">{skill.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function SkillsTree(props: SkillsTreeProps) {
  if (props.mode === 'select') {
    return <SkillsTreeSelectView {...props} />;
  }
  return <SkillsTreeManageView {...props} />;
}
