import type { TreeNode } from './client';

/** The vault as its tag groups, before it is a graph of notes.
 *
 * Drawing 4,300 note nodes at once produced a cloud, not a graph (operator,
 * 2026-10-24: "The Vault Loads alot of nodes Which make it not looking good …
 * we can Group the Vault By Tag Clicking on a Tag (Tag Parent) Drill down to
 * children"). So the graph view starts at the top of the tag tree: fifteen
 * bubbles instead of four thousand points, each sized by what is inside it.
 *
 * Deliberately NOT a force layout. There is nothing to simulate here — these
 * are counts, not links — and a bubble that drifts under the cursor is harder
 * to click than one that stays put. The force graph takes over once a branch
 * is chosen and the nodes are real notes with real edges between them.
 */
export function TagClusters({
  nodes,
  onDrillDown,
  heading,
}: {
  nodes: TreeNode[];
  onDrillDown: (path: string) => void;
  heading: string;
}) {
  if (nodes.length === 0) {
    return <p className="text-muted">Nothing here carries a tag yet.</p>;
  }

  const largest = Math.max(...nodes.map((node) => node.count));

  return (
    <div className="tag-clusters">
      <p className="text-muted tag-clusters-heading">{heading}</p>
      <div className="tag-cluster-grid">
        {nodes.map((node) => (
          <button
            type="button"
            key={node.path}
            className="tag-cluster"
            // Area by count, not diameter: a 2,700-note group next to a
            // 19-note one is 140x the area if you scale the radius, and the
            // small one disappears. The square root keeps both readable.
            style={{ '--cluster-scale': Math.sqrt(node.count / largest) } as React.CSSProperties}
            onClick={() => onDrillDown(node.path)}
          >
            <span className="tag-cluster-bubble" aria-hidden="true" />
            <span className="tag-cluster-name">{node.name}</span>
            <span className="tag-cluster-count">{node.count}</span>
            {node.children.length > 0 && (
              <span className="tag-cluster-children">{node.children.length} inside</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
