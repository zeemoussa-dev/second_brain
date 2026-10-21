import { useMemo, useState } from 'react';

interface Edge { from: string; to: string; when: string | null; declared: boolean }
interface AgentNode { id: string; name: string; routes_to: string[]; may_call: string[]; is_entry: boolean }
interface Door { label: string; source: string; chat_id: string; reaches: string | null }

interface Placed { id: string; label: string; column: number; x: number; y: number; kind: 'door' | 'agent' }

const COLUMN_WIDTH = 260;
const ROW_HEIGHT = 56;
const BOX_WIDTH = 210;
const BOX_HEIGHT = 34;
const MARGIN = 20;

/** The flow as a picture (`REQ-SB-102`: "a Visual Representation of
 * Hermes in full").
 *
 * **Laid out in columns by distance from a door**, not by any prettier
 * arrangement: the operator's question is "where does an ask GO", and
 * depth-from-the-outside is exactly that question turned into a
 * position. A force-directed blob would look more like a diagram and
 * answer less.
 *
 * **Only the connected part is drawn.** This install has 42 agents and
 * 23 edges; the ~30 agents nothing routes to would be 30 floating boxes
 * saying nothing, and would shrink the part that carries meaning. They
 * are counted underneath instead — invisible is not the same as
 * omitted, so the count is stated.
 *
 * **An edge with no condition is dashed.** Same line, same direction,
 * visibly unlabelled: the route exists either way, and the thing the
 * operator is hunting is which ones nobody has explained.
 */
export function FlowDiagram({
  doors,
  agents,
  edges,
  onPick,
}: {
  doors: Door[];
  agents: AgentNode[];
  edges: Edge[];
  onPick?: (agentId: string) => void;
}) {
  const [hovered, setHovered] = useState<string | null>(null);

  const layout = useMemo(() => {
    const byId = new Map(agents.map((a) => [a.id, a]));
    const childrenOf = new Map<string, string[]>();
    for (const edge of edges) {
      childrenOf.set(edge.from, [...(childrenOf.get(edge.from) ?? []), edge.to]);
    }

    // Column 0 is the doors. An agent's column is how many hops from one
    // it sits; an agent no door reaches but that something routes to
    // still gets placed, from its own parent.
    const column = new Map<string, number>();
    const queue: string[] = [];
    for (const door of doors) {
      if (door.reaches && byId.has(door.reaches)) {
        column.set(door.reaches, 1);
        queue.push(door.reaches);
      }
    }
    for (const parent of childrenOf.keys()) {
      if (!column.has(parent)) {
        const reachedByAnother = edges.some((e) => e.to === parent);
        if (!reachedByAnother) {
          column.set(parent, 1);
          queue.push(parent);
        }
      }
    }
    while (queue.length) {
      const id = queue.shift()!;
      for (const child of childrenOf.get(id) ?? []) {
        if (!column.has(child)) {
          column.set(child, (column.get(id) ?? 1) + 1);
          queue.push(child);
        }
      }
    }

    const placed: Placed[] = [];
    const perColumn = new Map<number, number>();
    const put = (id: string, label: string, col: number, kind: Placed['kind']) => {
      const row = perColumn.get(col) ?? 0;
      perColumn.set(col, row + 1);
      placed.push({
        id, label, column: col, kind,
        x: MARGIN + col * COLUMN_WIDTH,
        y: MARGIN + row * ROW_HEIGHT,
      });
    };

    doors.forEach((door) => put(`door:${door.chat_id}`, `${door.source}: ${door.label}`, 0, 'door'));
    [...column.entries()]
      .sort((a, b) => a[1] - b[1] || a[0].localeCompare(b[0]))
      .forEach(([id, col]) => put(id, byId.get(id)?.name ?? id, col, 'agent'));

    const at = new Map(placed.map((p) => [p.id, p]));
    const lines = edges
      .map((edge) => ({ edge, from: at.get(edge.from), to: at.get(edge.to) }))
      .filter((l) => l.from && l.to);
    const doorLines = doors
      .filter((d) => d.reaches && at.has(d.reaches))
      .map((d) => ({ from: at.get(`door:${d.chat_id}`)!, to: at.get(d.reaches!)! }));

    const width = MARGIN * 2 + (Math.max(0, ...placed.map((p) => p.column)) + 1) * COLUMN_WIDTH;
    const height = MARGIN * 2 + Math.max(1, ...[...perColumn.values()]) * ROW_HEIGHT;
    return { placed, lines, doorLines, width, height, drawn: column.size };
  }, [doors, agents, edges]);

  const undrawn = agents.length - layout.drawn;

  if (layout.drawn === 0) {
    return (
      <p className="auth-note" data-testid="flow-diagram-empty">
        Nothing to draw: no door reaches an agent and no agent routes to another.
      </p>
    );
  }

  return (
    <>
      <div className="flow-diagram-scroll">
        <svg
          data-testid="flow-diagram"
          width={layout.width}
          height={layout.height}
          role="img"
          aria-label="Entry points and the agents they route through"
        >
          {layout.doorLines.map((line, index) => (
            <line
              key={`door-${index}`}
              x1={line.from.x + BOX_WIDTH} y1={line.from.y + BOX_HEIGHT / 2}
              x2={line.to.x} y2={line.to.y + BOX_HEIGHT / 2}
              className="flow-link flow-link-door"
            />
          ))}
          {layout.lines.map(({ edge, from, to }) => (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={from!.x + BOX_WIDTH} y1={from!.y + BOX_HEIGHT / 2}
              x2={to!.x} y2={to!.y + BOX_HEIGHT / 2}
              className={
                'flow-link' +
                (edge.declared ? '' : ' flow-link-silent') +
                (hovered && (edge.from === hovered || edge.to === hovered) ? ' flow-link-lit' : '')
              }
            >
              <title>
                {edge.from} → {edge.to}
                {edge.when ? `\n\nWhen: ${edge.when}` : '\n\nNo condition said.'}
              </title>
            </line>
          ))}
          {layout.placed.map((node) => (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              className={
                `flow-node flow-node-${node.kind}` +
                (hovered === node.id ? ' flow-node-lit' : '')
              }
              onMouseEnter={() => setHovered(node.id)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => node.kind === 'agent' && onPick?.(node.id)}
            >
              <rect width={BOX_WIDTH} height={BOX_HEIGHT} rx={6} />
              <text x={10} y={BOX_HEIGHT / 2 + 4}>
                {node.label.length > 28 ? `${node.label.slice(0, 27)}…` : node.label}
              </text>
              <title>{node.id}</title>
            </g>
          ))}
        </svg>
      </div>
      <p className="auth-note" data-testid="flow-diagram-caption">
        {layout.drawn} agent{layout.drawn === 1 ? '' : 's'} drawn, left to right by how far
        they sit from an outside door. A dashed line is a route with no condition said.
        {undrawn > 0 && (
          <> {undrawn} agent{undrawn === 1 ? ' is' : 's are'} not drawn — nothing routes to
          them and no door reaches them, so they would be floating boxes.</>
        )}
      </p>
    </>
  );
}
