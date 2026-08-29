import { useState } from 'react';

// 2026-08-29 (operator: "bring all the tags and folder groups also in a
// tree and now we can select and save") -- groups the vault's real flat
// tag list (VaultManager.list_scope_suggestions()'s own {tag, count}[])
// into a real hierarchy by "/" segments, the same convention every real
// tag in this vault already follows (customer/adnoc, azure/architecture/
// data, ...). Only a segment that is ITSELF a real, existing tag gets a
// checkbox -- an intermediate group like "azure" is pure navigation, not
// a synthetic "select the whole group" concept nothing in the domain
// model backs.
interface TagTreeNode {
  segment: string;
  fullPath: string;
  isRealTag: boolean;
  count?: number;
  children: Map<string, TagTreeNode>;
}

function buildTagTree(tags: { tag: string; count: number }[]): TagTreeNode {
  const root: TagTreeNode = { segment: '', fullPath: '', isRealTag: false, children: new Map() };
  for (const { tag, count } of tags) {
    const parts = tag.split('/');
    let node = root;
    let path = '';
    for (const part of parts) {
      path = path ? `${path}/${part}` : part;
      let child = node.children.get(part);
      if (!child) {
        child = { segment: part, fullPath: path, isRealTag: false, children: new Map() };
        node.children.set(part, child);
      }
      node = child;
    }
    node.isRealTag = true;
    node.count = count;
  }
  return root;
}

interface TagTreePickerProps {
  tags: { tag: string; count: number }[];
  selectedTags: string[];
  onToggle: (tag: string) => void;
}

function TagTreeGroup({
  node,
  selectedTags,
  onToggle,
}: {
  node: TagTreeNode;
  selectedTags: string[];
  onToggle: (tag: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const children = Array.from(node.children.values());
  const hasChildren = children.length > 0;

  return (
    <div className="tag-tree-group" data-testid={`tag-tree-group-${node.fullPath}`}>
      <div className="tag-tree-row">
        {hasChildren && (
          <button
            type="button"
            className="tag-tree-toggle"
            aria-expanded={!collapsed}
            onClick={() => setCollapsed((value) => !value)}
          >
            {collapsed ? '▸' : '▾'}
          </button>
        )}
        {node.isRealTag ? (
          <label className="tag-tree-label">
            <input
              type="checkbox"
              checked={selectedTags.includes(node.fullPath)}
              onChange={() => onToggle(node.fullPath)}
            />
            <span>{node.segment}</span>
            {typeof node.count === 'number' && <span className="tag-tree-count">{node.count}</span>}
          </label>
        ) : (
          <span className="tag-tree-group-label">{node.segment}</span>
        )}
      </div>
      {hasChildren && !collapsed && (
        <div className="tag-tree-children">
          {children.map((child) => (
            <TagTreeGroup key={child.fullPath} node={child} selectedTags={selectedTags} onToggle={onToggle} />
          ))}
        </div>
      )}
    </div>
  );
}

export function TagTreePicker({ tags, selectedTags, onToggle }: TagTreePickerProps) {
  if (tags.length === 0) {
    return <p className="text-muted">No real tags found in the vault yet.</p>;
  }
  const root = buildTagTree(tags);
  const topLevel = Array.from(root.children.values());
  return (
    <div className="tag-tree" data-testid="tag-tree-picker">
      {topLevel.map((node) => (
        <TagTreeGroup key={node.fullPath} node={node} selectedTags={selectedTags} onToggle={onToggle} />
      ))}
    </div>
  );
}
