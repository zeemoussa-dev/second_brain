import { useMemo, useState } from 'react';

interface Edge { from: string; to: string; when: string | null; declared: boolean }
interface AgentNode {
  id: string;
  name: string;
  routes_to: string[];
  may_call: string[];
  is_entry: boolean;
  type?: string | null;
}
interface Door { label: string; source: string; chat_id: string; reaches: string | null }

interface Placed {
  id: string;
  label: string;
  sublabel: string;
  depth: number;
  x: number;
  y: number;
  kind: 'door' | 'agent';
  routes: number;
  actions: number;
  unconditioned: number;
}

const NODE_WIDTH = 210;
const NODE_HEIGHT = 66;
const COLUMN_GAP = 34;
/** Tall enough that a condition can be written ON the line between two rows,
 *  which is the whole reason the layout turned vertical. */
const ROW_HEIGHT = 150;
const MARGIN = 24;
const COLUMN_PITCH = NODE_WIDTH + COLUMN_GAP;

/** The flow as a picture (`REQ-SB-102`: "a Visual Representation of Hermes in
 * full"), read top to bottom.
 *
 * **Top to bottom, not left to right** (operator, 2026-10-24). The shape being
 * drawn is a hierarchy — a door, the agent it opens on, the specialists that
 * agent calls — and every other hierarchy a person reads runs downwards. It
 * also buys the thing the sideways version had nowhere to put: a gap between
 * rows wide enough to write the condition on the line.
 *
 * **Laid out by distance from a door**, not by any prettier arrangement: the
 * operator's question is "where does an ask GO", and depth-from-the-outside is
 * that question turned into a position. A force-directed blob would look more
 * like a diagram and answer less.
 *
 * **Each node carries its own numbers.** A box with only a name makes you
 * click it to learn anything, and with 42 agents that is 42 clicks to find the
 * one that is wrong. Specialist count, Action count and "nothing says when"
 * are the three facts the map exists to surface, so they are on the node.
 *
 * **The condition is written on the line, and its absence is a button.** An
 * edge with no `when` is dashed and offers "say when" — which is the whole
 * answer to "I can't find where to set the When": it is on the line that is
 * missing it, not on a form further down a different page.
 *
 * **Only the connected part is drawn.** This install has 42 agents and 23
 * edges; the ~30 agents nothing routes to would be floating boxes saying
 * nothing, and would shrink the part that carries meaning. They are counted
 * underneath instead — invisible is not the same as omitted.
 */
export function FlowDiagram({
  doors,
  agents,
  edges,
  onPick,
  onSayWhen,
}: {
  doors: Door[];
  agents: AgentNode[];
  edges: Edge[];
  onPick?: (agentId: string) => void;
  /** Called with the PARENT: the condition is written on the parent's own
   *  routing, so that is what the caller has to open. */
  onSayWhen?: (parentId: string, childId: string) => void;
}) {
  const [hovered, setHovered] = useState<string | null>(null);

  const layout = useMemo(() => {
    const byId = new Map(agents.map((agent) => [agent.id, agent]));
    const childrenOf = new Map<string, string[]>();
    for (const edge of edges) {
      childrenOf.set(edge.from, [...(childrenOf.get(edge.from) ?? []), edge.to]);
    }

    // Row 0 is the doors. An agent's row is how many hops from one it sits; an
    // agent no door reaches but that something routes to still gets placed,
    // from its own parent.
    const depth = new Map<string, number>();
    const queue: string[] = [];
    for (const door of doors) {
      if (door.reaches && byId.has(door.reaches)) {
        depth.set(door.reaches, 1);
        queue.push(door.reaches);
      }
    }
    for (const parent of childrenOf.keys()) {
      if (!depth.has(parent) && !edges.some((edge) => edge.to === parent)) {
        depth.set(parent, 1);
        queue.push(parent);
      }
    }
    while (queue.length) {
      const id = queue.shift()!;
      for (const child of childrenOf.get(id) ?? []) {
        if (!depth.has(child)) {
          depth.set(child, (depth.get(id) ?? 1) + 1);
          queue.push(child);
        }
      }
    }

    const placed: Placed[] = [];
    const perRow = new Map<number, number>();
    const put = (
      id: string,
      label: string,
      sublabel: string,
      row: number,
      kind: Placed['kind'],
      counts: { routes: number; actions: number; unconditioned: number },
    ) => {
      const column = perRow.get(row) ?? 0;
      perRow.set(row, column + 1);
      placed.push({
        id, label, sublabel, depth: row, kind, ...counts,
        x: MARGIN + column * COLUMN_PITCH,
        y: MARGIN + row * ROW_HEIGHT,
      });
    };

    doors.forEach((door) =>
      put(`door:${door.chat_id}`, door.label, door.source, 0, 'door',
        { routes: 0, actions: 0, unconditioned: 0 }),
    );
    [...depth.entries()]
      .sort((a, b) => a[1] - b[1] || a[0].localeCompare(b[0]))
      .forEach(([id, row]) => {
        const agent = byId.get(id);
        const out = edges.filter((edge) => edge.from === id);
        put(id, agent?.name ?? id, agent?.type ?? id, row, 'agent', {
          routes: out.length,
          actions: agent?.may_call.length ?? 0,
          unconditioned: out.filter((edge) => !edge.when).length,
        });
      });

    // Rows are centred against the widest one, so a single child sits under
    // its parent instead of hard against the left edge.
    const widest = Math.max(1, ...[...perRow.values()]);
    const rowWidth = (count: number) => count * COLUMN_PITCH - COLUMN_GAP;
    const fullWidth = rowWidth(widest);
    for (const node of placed) {
      const count = perRow.get(node.depth) ?? 1;
      node.x += (fullWidth - rowWidth(count)) / 2;
    }

    const at = new Map(placed.map((node) => [node.id, node]));
    const lines = edges
      .map((edge) => ({ edge, from: at.get(edge.from), to: at.get(edge.to) }))
      .filter((line) => line.from && line.to);
    const doorLines = doors
      .filter((door) => door.reaches && at.has(door.reaches))
      .map((door) => ({ from: at.get(`door:${door.chat_id}`)!, to: at.get(door.reaches!)! }));

    return {
      placed,
      lines,
      doorLines,
      width: MARGIN * 2 + fullWidth,
      height: MARGIN * 2 + (Math.max(0, ...placed.map((node) => node.depth)) + 1) * ROW_HEIGHT
        - (ROW_HEIGHT - NODE_HEIGHT),
      drawn: depth.size,
    };
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
          aria-label="Entry points and the agents they route through, top to bottom"
        >
          <defs>
            {/* Direction has to be visible on a vertical line: between two rows
                of boxes, a plain segment reads as a join, not a journey. */}
            <marker
              id="flow-arrow"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" className="flow-arrow-head" />
            </marker>
          </defs>

          {layout.doorLines.map((line, index) => (
            <path
              key={`door-${index}`}
              d={curveBetween(line.from, line.to)}
              className="flow-link flow-link-door"
              markerEnd="url(#flow-arrow)"
            />
          ))}

          {layout.lines.map(({ edge, from, to }) => {
            const lit = hovered === edge.from || hovered === edge.to;
            const mid = midpointOf(from!, to!);
            return (
              <g key={`${edge.from}-${edge.to}`}>
                <path
                  d={curveBetween(from!, to!)}
                  className={
                    'flow-link' +
                    (edge.when ? '' : ' flow-link-silent') +
                    (lit ? ' flow-link-lit' : '')
                  }
                  markerEnd="url(#flow-arrow)"
                >
                  <title>
                    {edge.from} → {edge.to}
                    {edge.when ? `\n\nWhen: ${edge.when}` : '\n\nNo condition said.'}
                  </title>
                </path>
                {edge.when ? (
                  <EdgeCondition x={mid.x} y={mid.y} text={edge.when} />
                ) : (
                  <g
                    className="flow-when-missing"
                    transform={`translate(${mid.x - 44}, ${mid.y - 11})`}
                    onClick={() => onSayWhen?.(edge.from, edge.to)}
                    role={onSayWhen ? 'button' : undefined}
                  >
                    <rect width={88} height={22} rx={11} />
                    <text x={44} y={15}>say when</text>
                    <title>Nothing records why an ask should take this route. Click to write it.</title>
                  </g>
                )}
              </g>
            );
          })}

          {layout.placed.map((node) => (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              className={
                `flow-node flow-node-${node.kind}` +
                (hovered === node.id ? ' flow-node-lit' : '') +
                (node.unconditioned > 0 ? ' flow-node-incomplete' : '')
              }
              onMouseEnter={() => setHovered(node.id)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => node.kind === 'agent' && onPick?.(node.id)}
              role={node.kind === 'agent' && onPick ? 'button' : undefined}
            >
              <rect width={NODE_WIDTH} height={NODE_HEIGHT} rx={10} />
              <text className="flow-node-name" x={12} y={25}>
                {clip(node.label, 26)}
              </text>
              <text className="flow-node-sub" x={12} y={42}>
                {clip(node.sublabel, 30)}
              </text>
              {node.kind === 'agent' && (
                <text className="flow-node-counts" x={12} y={58}>
                  {node.routes} specialist{node.routes === 1 ? '' : 's'} · {node.actions} action
                  {node.actions === 1 ? '' : 's'}
                  {node.unconditioned > 0 ? ` · ${node.unconditioned} unexplained` : ''}
                </text>
              )}
              <title>{node.id}</title>
            </g>
          ))}
        </svg>
      </div>
      <p className="auth-note" data-testid="flow-diagram-caption">
        {layout.drawn} agent{layout.drawn === 1 ? '' : 's'} drawn, top to bottom by how far they
        sit from an outside door. A dashed line is a route nobody has explained — the{' '}
        <strong>say when</strong> on it writes the condition.
        {undrawn > 0 && (
          <> {undrawn} agent{undrawn === 1 ? ' is' : 's are'} not drawn — nothing routes to them
          and no door reaches them, so they would be floating boxes.</>
        )}
      </p>
    </>
  );
}

/** A condition, written on the line it belongs to. Two lines at most: this is
 *  a label on a diagram, and an operator who wants the whole sentence has the
 *  editor and the tooltip. */
function EdgeCondition({ x, y, text }: { x: number; y: number; text: string }) {
  const shown = clip(text, 34);
  const width = Math.min(200, Math.max(70, shown.length * 6.2));
  return (
    <g className="flow-when" transform={`translate(${x - width / 2}, ${y - 11})`}>
      <rect width={width} height={22} rx={11} />
      <text x={width / 2} y={15}>{shown}</text>
      <title>{text}</title>
    </g>
  );
}

/** Bottom of the parent to the top of the child, bending vertically. Straight
 *  lines between staggered rows cross each other at angles that read as
 *  noise; a curve that leaves downward and arrives downward keeps the
 *  direction legible even where several lines converge. */
function curveBetween(from: { x: number; y: number }, to: { x: number; y: number }): string {
  const startX = from.x + NODE_WIDTH / 2;
  const startY = from.y + NODE_HEIGHT;
  const endX = to.x + NODE_WIDTH / 2;
  const endY = to.y;
  const bend = Math.max(24, (endY - startY) / 2);
  return `M ${startX} ${startY} C ${startX} ${startY + bend}, ${endX} ${endY - bend}, ${endX} ${endY}`;
}

function midpointOf(from: { x: number; y: number }, to: { x: number; y: number }) {
  return {
    x: (from.x + to.x) / 2 + NODE_WIDTH / 2,
    y: (from.y + NODE_HEIGHT + to.y) / 2,
  };
}

function clip(text: string, limit: number): string {
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}
