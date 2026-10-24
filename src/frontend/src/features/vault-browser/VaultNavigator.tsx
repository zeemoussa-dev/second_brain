import { useState } from 'react';
import type { TreeNode } from './client';

/** Where a note is, as something you can walk (operator, 2026-10-24: tags
 *  "Should be Shown By Category not every single Tag", and notes should have
 *  "a Folder Display to Navigate or Tag Display to Navigate").
 *
 * This vault has 312 distinct tags across 15 top-level categories and folders
 * eight deep — a flat row of chips was a screenful before the notes started.
 * Tags and folders are the same thing to navigate (a path, a count, children),
 * so they are one component with two sources rather than two trees to keep in
 * step.
 *
 * Opening a branch and SELECTING it are separate: the chevron expands, the
 * name filters. Tying them together means you cannot look inside `customer`
 * without filtering to it, and cannot filter to it without the list jumping
 * under the branch you were reading.
 */
export function VaultNavigator({
  nodes,
  selected,
  onSelect,
  emptyLabel,
}: {
  nodes: TreeNode[];
  selected: string | null;
  onSelect: (path: string | null) => void;
  emptyLabel: string;
}) {
  if (nodes.length === 0) {
    return <p className="text-muted nav-tree-empty">{emptyLabel}</p>;
  }

  return (
    <nav className="nav-tree" aria-label="Narrow by">
      <button
        type="button"
        className={`nav-tree-row ${selected === null ? 'is-selected' : ''}`}
        onClick={() => onSelect(null)}
      >
        <span className="nav-tree-spacer" />
        <span className="nav-tree-name">Everything</span>
      </button>
      {nodes.map((node) => (
        <TreeBranch key={node.path} node={node} depth={0} selected={selected} onSelect={onSelect} />
      ))}
    </nav>
  );
}

function TreeBranch({
  node,
  depth,
  selected,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  selected: string | null;
  onSelect: (path: string | null) => void;
}) {
  // A branch opens when the selection is inside it, so arriving by URL on
  // `customer/masdar` shows that row rather than a collapsed `customer`.
  const holdsSelection = selected !== null && (selected === node.path || selected.startsWith(node.path + '/'));
  const [open, setOpen] = useState(holdsSelection);
  const hasChildren = node.children.length > 0;
  const isSelected = selected === node.path;

  return (
    <>
      <div className={`nav-tree-row ${isSelected ? 'is-selected' : ''}`} style={{ paddingLeft: depth * 14 }}>
        {hasChildren ? (
          <button
            type="button"
            className="nav-tree-toggle"
            aria-expanded={open}
            aria-label={`${open ? 'Collapse' : 'Expand'} ${node.name}`}
            onClick={() => setOpen((wasOpen) => !wasOpen)}
          >
            <span className="material-symbols-outlined" aria-hidden="true">
              {open ? 'expand_more' : 'chevron_right'}
            </span>
          </button>
        ) : (
          <span className="nav-tree-spacer" />
        )}
        <button
          type="button"
          className="nav-tree-name"
          aria-current={isSelected ? 'true' : undefined}
          onClick={() => onSelect(isSelected ? null : node.path)}
          title={node.path}
        >
          {node.name}
        </button>
        <span className="nav-tree-count">{node.count}</span>
      </div>
      {open &&
        node.children.map((child) => (
          <TreeBranch
            key={child.path}
            node={child}
            depth={depth + 1}
            selected={selected}
            onSelect={onSelect}
          />
        ))}
    </>
  );
}
