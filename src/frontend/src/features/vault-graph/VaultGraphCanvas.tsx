import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router';
import type { VaultGraphEdge, VaultGraphNode } from './client';
import { createInitialNodes, tickSimulation, type SimulationNode } from './forceLayout';

interface VaultGraphCanvasProps {
  // Already filtered by the caller (kind-filter/search state lives in
  // VaultGraphPage.tsx, T03) — this component is purely presentational,
  // mirroring AgentsMapCanvas.tsx's own "driven by props" shape.
  nodes: VaultGraphNode[];
  edges: VaultGraphEdge[];
}

// Graph-space node draw radius, now degree-scaled (2026-08-23, operator:
// "The Circle Size Should be Linked to the Amount of links or Mentions
// for the file") — click hit-testing (findNodeNear) uses each node's own
// real drawn radius, not this flat constant, converted through the
// current pan/zoom transform. sqrt(degree), not linear, for the same
// "one extreme hub shouldn't dwarf the screen" reasoning as
// forceLayout.ts's own DEGREE_CENTERING_FACTOR.
const NODE_RADIUS_MIN = 4;
const NODE_RADIUS_MAX = 22;
const NODE_RADIUS_DEGREE_SCALE = 2.2;

function radiusForDegree(degree: number): number {
  return Math.min(NODE_RADIUS_MAX, NODE_RADIUS_MIN + Math.sqrt(degree) * NODE_RADIUS_DEGREE_SCALE);
}

// Visual-only shrink (2026-08-23, operator: "the Nodes it self is very
// big leaving no Space for the lines to be Visible... Shrinking the
// nodes by 50% while Maintaining there Positions") -- deliberately NOT
// a change to radiusForDegree/simNode.radius itself, which still governs
// collision spacing (forceLayout.ts) and click hit-testing
// (findNodeNear): shrinking THAT would let the physics pack circles into
// a tighter footprint, moving every node's real position to fill the
// newly-available room -- the opposite of "maintaining positions". This
// constant only scales the drawn arc radius at the two draw call sites
// below, so each circle now sits smaller inside the SAME personal-space
// bubble collision resolution already reserved for it -- position
// unchanged, real visible gap opens up around it for edges to read
// through.
const NODE_DRAW_SCALE = 0.5;

const KIND_COLOR_SLOT_COUNT = 8;
// Density solution (2026-08-23, operator: "The Lines are very Dense need
// to think about a solution") — mirrors Obsidian's own graph view, the
// direct visual precedent for this screen: every edge renders at a very
// low base opacity by default (dense areas read as a soft haze instead
// of a solid mess), and hovering a node brightens/thickens ONLY that
// node's own real edges while dimming every other edge further —
// letting a viewer actually trace one note's real connections out of
// thousands, on demand, instead of drawing every edge at equal, always-
// cluttered strength.
const EDGE_ALPHA_BASE = 0.06;
// Dropped 0.02 -> 0.006 (2026-08-23, operator: "the not Hover [nodes]
// and the lines that are not connected are mixing... if you gonna Dim
// the nodes we need to dim the lines"). The dimmed background NODES
// (NORMAL_NODE_ALPHA_WHEN_HOVERING = 0.15) and the dimmed background
// EDGES weren't receding at comparable rates -- with most of the
// graph's 6,032 real edges NOT touching whichever node is hovered,
// thousands of still-somewhat-visible lines kept crossing behind/through
// the dimmed nodes, reading as one blended, still-busy mass rather than
// a clearly quiet background the lit-up hovered node + its neighbors
// stand apart from. Low enough now to be practically invisible on its
// own, so the background genuinely recedes as a unit.
const EDGE_ALPHA_DIMMED = 0.006;
// Softened 0.9/2 -> 0.55/1.25 (2026-08-23, operator: "Lines on hover are
// very thick need to be more visually Appealing") -- a genuinely
// hub-connected note can highlight hundreds of edges at once fanning out
// from one point; near-opaque + 2x width read as one solid wedge rather
// than individually legible lines. Still clearly brighter/thicker than
// the base haze, just not a wall.
const EDGE_ALPHA_HIGHLIGHT = 0.55;
const EDGE_WIDTH_HIGHLIGHT = 1.25;
// Hover label (2026-08-23, operator: "The Nodes Hover Effect should...
// have the name of the node visible") -- drawn inside the SAME
// context.scale()'d transform as every node/edge, so fillText's own
// apparent screen size scales with zoom exactly like a stroke width
// does. Both constants below are graph-space px, divided by
// scaleRef.current at draw time (mirroring the existing edge-width
// convention) so the label reads as the SAME real screen size at any
// zoom level, not shrinking/growing with it.
const HOVER_LABEL_FONT_PX = 13;
const HOVER_LABEL_OFFSET_PX = 10;
// Neighbor highlight (2026-08-23, operator: "this will [give] me a
// chance to see who they are connected with and Highlight the connected
// node with something like hover effect but different, think about
// it") -- a THIRD distinct visual tier, not a copy of the hovered node's
// own treatment: everything NOT connected to the hovered node dims well
// below its own normal resting opacity (so the connected set visually
// pops as an island against a quiet background, the actual "who is this
// connected to" answer at a glance); each real neighbor gets a thin ring
// in the same highlight color the edges themselves use (ties the ring
// visually to "this is lit up because of that bright line", rather than
// reusing the hovered node's own text-colored ring, which would make
// the two tiers hard to tell apart at a glance) but stays at its
// own normal (un-enlarged) size -- the hovered node alone gets bigger/
// frontmost treatment, so there's never any ambiguity about which ONE
// node is actually being pointed at. Neighbor NAME labels only draw
// when the neighbor count is small enough to stay legible
// (NEIGHBOR_LABEL_MAX_COUNT) -- a true hub can have hundreds of real
// connections, and unconditionally drawing hundreds of overlapping text
// labels would recreate exactly the illegible-clutter problem the whole
// hover-highlight feature exists to solve.
const NORMAL_NODE_ALPHA_WHEN_HOVERING = 0.15;
const NEIGHBOR_RING_WIDTH = 1;
const NEIGHBOR_LABEL_MAX_COUNT = 25;
const NEIGHBOR_LABEL_FONT_PX = 11;
const NEIGHBOR_LABEL_OFFSET_PX = 6;
// Re-settle strength on a drag interaction — high enough that dragging one
// node visibly nudges its immediate neighborhood, without fully
// re-randomizing the whole layout every time.
const DRAG_ALPHA_RESET = 0.6;
// Screen-pixel movement below this, between pointerdown and pointerup, is
// treated as a click (navigate), not a drag/pan.
const CLICK_MOVEMENT_THRESHOLD_PX = 4;
const MIN_ZOOM_SCALE = 0.15;
const MAX_ZOOM_SCALE = 6;

/** Deterministic string hash -> one of the 8 --graph-kind-color-* slots
 * (tokens.css). Must never enumerate specific kind names (Customer,
 * Thread, ...) so any real, current-or-future `frontmatter.type` value
 * resolves to a valid slot. */
function hashKindToSlotIndex(kind: string): number {
  let hash = 0;
  for (let charIndex = 0; charIndex < kind.length; charIndex += 1) {
    hash = (hash * 31 + kind.charCodeAt(charIndex)) | 0;
  }
  return Math.abs(hash) % KIND_COLOR_SLOT_COUNT;
}

export function VaultGraphCanvas({ nodes, edges }: VaultGraphCanvasProps) {
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const simulationNodesRef = useRef<Map<string, SimulationNode>>(new Map());
  const alphaRef = useRef(1);
  const kindColorCacheRef = useRef<Map<string, string>>(new Map());
  // Populated from --graph-edge-color via getComputedStyle before the
  // first animation frame draws (the color-reading effect below runs
  // first) — starts empty, never a hardcoded color literal.
  const edgeColorRef = useRef('');
  // Hover label text color, same read-from-tokens.css convention as
  // edgeColorRef/kindColorCacheRef above.
  const textColorRef = useRef('');
  // Neighbor-highlight ring color -- deliberately a THIRD, visually
  // distinct color from both textColorRef (the hovered node's own ring)
  // and edgeColorRef (near-identical pale cream tones that would make
  // the two highlight tiers hard to tell apart) -- --color-accent is
  // this app's own established "active/selected" hue elsewhere.
  const accentColorRef = useRef('');
  const panRef = useRef({ x: 0, y: 0 });
  const scaleRef = useRef(1);
  // Hover-to-highlight (density solution above) — tracked in a ref, not
  // React state: the draw loop reads it once per animation frame, so a
  // state-driven re-render on every pointer-move would be pure churn.
  const hoveredStemRef = useRef<string | null>(null);
  const dragRef = useRef<{
    mode: 'node' | 'pan';
    stem: string | null;
    startScreenX: number;
    startScreenY: number;
    startPanX: number;
    startPanY: number;
    moved: boolean;
  } | null>(null);

  // Every color this component draws is read from tokens.css via
  // getComputedStyle — <canvas> has no CSS cascade of its own, so this is
  // the only way to keep zero hardcoded color literals here while still
  // supporting the rotating 8-slot palette (AC-06).
  useEffect(() => {
    const rootStyles = getComputedStyle(document.documentElement);
    const cache = new Map<string, string>();
    for (let slot = 1; slot <= KIND_COLOR_SLOT_COUNT; slot += 1) {
      cache.set(`slot-${slot}`, rootStyles.getPropertyValue(`--graph-kind-color-${slot}`).trim());
    }
    kindColorCacheRef.current = cache;
    edgeColorRef.current = rootStyles.getPropertyValue('--graph-edge-color').trim();
    textColorRef.current = rootStyles.getPropertyValue('--color-text').trim();
    accentColorRef.current = rootStyles.getPropertyValue('--color-accent').trim();
  }, []);

  function colorForKind(kind: string): string {
    const slotIndex = hashKindToSlotIndex(kind);
    return kindColorCacheRef.current.get(`slot-${slotIndex + 1}`) || edgeColorRef.current;
  }

  // Sync the simulation's own node set whenever the caller's filtered
  // nodes prop changes (kind filter toggle, search term) — nodes still
  // present keep their existing position (no jarring re-layout on a
  // no-op filter round trip); newly-visible nodes join at a position
  // derived from the current canvas size. Also (re)computes every
  // node's own real `degree` from the CURRENT edge list, so toggling a
  // kind filter or searching immediately re-scales circle size/centering
  // pull to match the edges actually visible right now, not a stale
  // full-graph count.
  useEffect(() => {
    const canvas = canvasRef.current;
    const width = canvas?.clientWidth || 800;
    const height = canvas?.clientHeight || 600;
    const nextStems = new Set(nodes.map((node) => node.stem));
    const existing = simulationNodesRef.current;

    for (const stem of Array.from(existing.keys())) {
      if (!nextStems.has(stem)) existing.delete(stem);
    }

    const newStems = nodes.filter((node) => !existing.has(node.stem)).map((node) => node.stem);
    if (newStems.length > 0) {
      for (const simNode of createInitialNodes(newStems, width, height)) {
        existing.set(simNode.stem, simNode);
      }
    }

    const degreeByStem = new Map<string, number>();
    for (const edge of edges) {
      if (!nextStems.has(edge.source) || !nextStems.has(edge.target)) continue;
      degreeByStem.set(edge.source, (degreeByStem.get(edge.source) ?? 0) + 1);
      degreeByStem.set(edge.target, (degreeByStem.get(edge.target) ?? 0) + 1);
    }
    for (const simNode of existing.values()) {
      const degree = degreeByStem.get(simNode.stem) ?? 0;
      simNode.degree = degree;
      // Copied onto the node itself (not recomputed per-frame) so
      // forceLayout.ts's own collision-resolution pass can read a real
      // radius without needing to know the size FORMULA at all.
      simNode.radius = radiusForDegree(degree);
    }

    alphaRef.current = Math.max(alphaRef.current, 0.5);
  }, [nodes, edges]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext('2d');
    if (!context) return;

    let animationFrameId: number;
    const nodeByStem = new Map(nodes.map((node) => [node.stem, node]));

    function resizeCanvasToContainer() {
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
    }

    function draw() {
      if (!canvas || !context) return;
      const width = canvas.width;
      const height = canvas.height;
      const simNodes = Array.from(simulationNodesRef.current.values());
      const simEdges = edges.filter((edge) => nodeByStem.has(edge.source) && nodeByStem.has(edge.target));

      const { alpha } = tickSimulation(simNodes, simEdges, width, height, alphaRef.current);
      alphaRef.current = alpha;

      context.clearRect(0, 0, width, height);
      context.save();
      context.translate(panRef.current.x, panRef.current.y);
      context.scale(scaleRef.current, scaleRef.current);

      // Density solution (2026-08-23, operator: "The Lines are very
      // Dense need to think about a solution") — two passes so the
      // hovered node's own real edges always paint OVER the low-opacity
      // haze of every other edge, instead of z-order depending on
      // whichever happened to be pushed onto simEdges last.
      const hoveredStem = hoveredStemRef.current;
      context.strokeStyle = edgeColorRef.current;
      context.lineWidth = 1 / scaleRef.current;
      for (const edge of simEdges) {
        if (hoveredStem && (edge.source === hoveredStem || edge.target === hoveredStem)) continue;
        const source = simulationNodesRef.current.get(edge.source);
        const target = simulationNodesRef.current.get(edge.target);
        if (!source || !target) continue;
        context.globalAlpha = hoveredStem ? EDGE_ALPHA_DIMMED : EDGE_ALPHA_BASE;
        context.beginPath();
        context.moveTo(source.x, source.y);
        context.lineTo(target.x, target.y);
        context.stroke();
      }
      if (hoveredStem) {
        context.lineWidth = EDGE_WIDTH_HIGHLIGHT / scaleRef.current;
        context.globalAlpha = EDGE_ALPHA_HIGHLIGHT;
        for (const edge of simEdges) {
          if (edge.source !== hoveredStem && edge.target !== hoveredStem) continue;
          const source = simulationNodesRef.current.get(edge.source);
          const target = simulationNodesRef.current.get(edge.target);
          if (!source || !target) continue;
          context.beginPath();
          context.moveTo(source.x, source.y);
          context.lineTo(target.x, target.y);
          context.stroke();
        }
      }
      context.globalAlpha = 1;

      // Three-tier node hover treatment (2026-08-23, operator: "this
      // will [give] me a chance to see who they are connected with and
      // Highlight the connected node with something like hover effect
      // but different, think about it"). Tier 1 (everything else): dims
      // well below normal resting opacity while a hover is active, so
      // the connected set reads as a lit island against a quiet
      // background. Tier 2 (real neighbors -- an edge actually connects
      // them to the hovered node): stays at full opacity/normal size,
      // gets its own thin ACCENT-colored ring (deliberately not the same
      // color as the hovered node's own ring below, so the two tiers
      // never look like the same thing) and its real title, but ONLY
      // when there are few enough neighbors for labels to stay legible
      // (NEIGHBOR_LABEL_MAX_COUNT) -- a true hub can have hundreds of
      // real connections, and unconditionally drawing hundreds of
      // overlapping labels would recreate the exact clutter this feature
      // exists to cut through. Tier 3 (the hovered node itself): drawn
      // strictly last/on top, enlarged ring, own label -- unchanged from
      // the previous pass, still the one unambiguous focal point.
      // All three passes draw at NODE_DRAW_SCALE (operator: "the Nodes
      // itself is very big... Shrinking the nodes by 50% while
      // Maintaining there Positions") -- visual size only; the
      // UNSCALED node.radius still governs collision spacing
      // (forceLayout.ts) and click hit-testing (findNodeNear) below, so
      // real positions/click targets don't shift, just the circle drawn
      // inside each one's own already-reserved space shrinks, opening
      // real visible gaps for edges to read through.
      const neighborStems = new Set<string>();
      if (hoveredStem) {
        for (const edge of simEdges) {
          if (edge.source === hoveredStem) neighborStems.add(edge.target);
          else if (edge.target === hoveredStem) neighborStems.add(edge.source);
        }
      }
      const showNeighborLabels = neighborStems.size > 0 && neighborStems.size <= NEIGHBOR_LABEL_MAX_COUNT;

      let hoveredNode: SimulationNode | null = null;
      let hoveredMeta: VaultGraphNode | null = null;
      const neighborEntries: { node: SimulationNode; meta: VaultGraphNode }[] = [];
      for (const node of simNodes) {
        const meta = nodeByStem.get(node.stem);
        if (!meta) continue;
        if (node.stem === hoveredStem) {
          hoveredNode = node;
          hoveredMeta = meta;
          continue;
        }
        if (neighborStems.has(node.stem)) {
          neighborEntries.push({ node, meta });
          continue;
        }
        context.globalAlpha = hoveredStem ? NORMAL_NODE_ALPHA_WHEN_HOVERING : 1;
        context.beginPath();
        context.fillStyle = colorForKind(meta.kind);
        context.arc(node.x, node.y, (node.radius ?? NODE_RADIUS_MIN) * NODE_DRAW_SCALE, 0, Math.PI * 2);
        context.fill();
      }

      context.globalAlpha = 1;
      for (const { node, meta } of neighborEntries) {
        const radius = (node.radius ?? NODE_RADIUS_MIN) * NODE_DRAW_SCALE;
        context.beginPath();
        context.fillStyle = colorForKind(meta.kind);
        context.arc(node.x, node.y, radius, 0, Math.PI * 2);
        context.fill();
        context.lineWidth = NEIGHBOR_RING_WIDTH / scaleRef.current;
        context.strokeStyle = accentColorRef.current;
        context.stroke();
        if (showNeighborLabels) {
          context.font = `${NEIGHBOR_LABEL_FONT_PX / scaleRef.current}px sans-serif`;
          context.fillStyle = accentColorRef.current;
          context.textAlign = 'left';
          context.textBaseline = 'middle';
          context.fillText(
            meta.title,
            node.x + radius + NEIGHBOR_LABEL_OFFSET_PX / scaleRef.current,
            node.y,
          );
        }
      }

      if (hoveredNode && hoveredMeta) {
        const radius = (hoveredNode.radius ?? NODE_RADIUS_MIN) * NODE_DRAW_SCALE;
        context.beginPath();
        context.fillStyle = colorForKind(hoveredMeta.kind);
        context.arc(hoveredNode.x, hoveredNode.y, radius, 0, Math.PI * 2);
        context.fill();
        // A thin ring around the hovered circle -- makes "this is the
        // one you're pointing at" unambiguous even where it overlaps
        // same-color neighbors, not just "on top" in paint order.
        context.lineWidth = 1.5 / scaleRef.current;
        context.strokeStyle = textColorRef.current;
        context.stroke();

        context.font = `${HOVER_LABEL_FONT_PX / scaleRef.current}px sans-serif`;
        context.fillStyle = textColorRef.current;
        context.textAlign = 'left';
        context.textBaseline = 'middle';
        context.fillText(
          hoveredMeta.title,
          hoveredNode.x + radius + HOVER_LABEL_OFFSET_PX / scaleRef.current,
          hoveredNode.y,
        );
      }

      context.restore();
      animationFrameId = requestAnimationFrame(draw);
    }

    resizeCanvasToContainer();
    const resizeObserver = new ResizeObserver(resizeCanvasToContainer);
    resizeObserver.observe(canvas);
    animationFrameId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();
    };
  }, [nodes, edges]);

  function graphPointFromEvent(event: React.PointerEvent<HTMLCanvasElement>): { x: number; y: number } {
    const rect = event.currentTarget.getBoundingClientRect();
    const screenX = event.clientX - rect.left;
    const screenY = event.clientY - rect.top;
    return {
      x: (screenX - panRef.current.x) / scaleRef.current,
      y: (screenY - panRef.current.y) / scaleRef.current,
    };
  }

  function findNodeNear(graphX: number, graphY: number): SimulationNode | null {
    for (const node of simulationNodesRef.current.values()) {
      const hitRadius = (node.radius ?? NODE_RADIUS_MIN) + 3;
      const dx = node.x - graphX;
      const dy = node.y - graphY;
      if (dx * dx + dy * dy <= hitRadius * hitRadius) return node;
    }
    return null;
  }

  function handlePointerDown(event: React.PointerEvent<HTMLCanvasElement>) {
    const graphPoint = graphPointFromEvent(event);
    const hitNode = findNodeNear(graphPoint.x, graphPoint.y);
    event.currentTarget.setPointerCapture(event.pointerId);
    if (hitNode) {
      hitNode.fixed = true;
      alphaRef.current = Math.max(alphaRef.current, DRAG_ALPHA_RESET);
      dragRef.current = {
        mode: 'node',
        stem: hitNode.stem,
        startScreenX: event.clientX,
        startScreenY: event.clientY,
        startPanX: panRef.current.x,
        startPanY: panRef.current.y,
        moved: false,
      };
    } else {
      dragRef.current = {
        mode: 'pan',
        stem: null,
        startScreenX: event.clientX,
        startScreenY: event.clientY,
        startPanX: panRef.current.x,
        startPanY: panRef.current.y,
        moved: false,
      };
    }
  }

  function handlePointerMove(event: React.PointerEvent<HTMLCanvasElement>) {
    const drag = dragRef.current;
    if (!drag) {
      // Not dragging — this move is purely hover tracking for the
      // density solution's own highlight-on-hover (draw()'s own
      // hoveredStemRef read, above). Cheap: canvas.getContext('2d')
      // isn't touched here, no re-render triggered (a plain ref write).
      const graphPoint = graphPointFromEvent(event);
      hoveredStemRef.current = findNodeNear(graphPoint.x, graphPoint.y)?.stem ?? null;
      return;
    }
    const deltaX = event.clientX - drag.startScreenX;
    const deltaY = event.clientY - drag.startScreenY;
    if (Math.abs(deltaX) > CLICK_MOVEMENT_THRESHOLD_PX || Math.abs(deltaY) > CLICK_MOVEMENT_THRESHOLD_PX) {
      drag.moved = true;
    }
    if (drag.mode === 'node' && drag.stem) {
      const node = simulationNodesRef.current.get(drag.stem);
      if (node) {
        const graphPoint = graphPointFromEvent(event);
        node.x = graphPoint.x;
        node.y = graphPoint.y;
        node.vx = 0;
        node.vy = 0;
      }
    } else if (drag.mode === 'pan') {
      panRef.current = { x: drag.startPanX + deltaX, y: drag.startPanY + deltaY };
    }
  }

  function handlePointerUp(event: React.PointerEvent<HTMLCanvasElement>) {
    const drag = dragRef.current;
    dragRef.current = null;
    if (!drag) return;
    event.currentTarget.releasePointerCapture(event.pointerId);
    if (drag.mode === 'node' && drag.stem) {
      const node = simulationNodesRef.current.get(drag.stem);
      if (node) node.fixed = false;
      if (!drag.moved) {
        navigate(`/browse/${encodeURIComponent(drag.stem)}`);
      }
    }
  }

  function handleWheel(event: React.WheelEvent<HTMLCanvasElement>) {
    event.preventDefault();
    const zoomFactor = event.deltaY < 0 ? 1.1 : 1 / 1.1;
    scaleRef.current = Math.min(MAX_ZOOM_SCALE, Math.max(MIN_ZOOM_SCALE, scaleRef.current * zoomFactor));
  }

  function handlePointerLeave() {
    hoveredStemRef.current = null;
  }

  return (
    <canvas
      ref={canvasRef}
      className="vault-graph-canvas"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerLeave}
      onWheel={handleWheel}
    />
  );
}
