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

// Graph-space node draw radius — click hit-testing uses the same
// constant, converted through the current pan/zoom transform.
const NODE_RADIUS = 6;
const KIND_COLOR_SLOT_COUNT = 8;
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
  const panRef = useRef({ x: 0, y: 0 });
  const scaleRef = useRef(1);
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
  }, []);

  function colorForKind(kind: string): string {
    const slotIndex = hashKindToSlotIndex(kind);
    return kindColorCacheRef.current.get(`slot-${slotIndex + 1}`) || edgeColorRef.current;
  }

  // Sync the simulation's own node set whenever the caller's filtered
  // nodes prop changes (kind filter toggle, search term) — nodes still
  // present keep their existing position (no jarring re-layout on a
  // no-op filter round trip); newly-visible nodes join at a position
  // derived from the current canvas size.
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
    alphaRef.current = Math.max(alphaRef.current, 0.5);
  }, [nodes]);

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

      context.strokeStyle = edgeColorRef.current;
      context.lineWidth = 1 / scaleRef.current;
      for (const edge of simEdges) {
        const source = simulationNodesRef.current.get(edge.source);
        const target = simulationNodesRef.current.get(edge.target);
        if (!source || !target) continue;
        context.beginPath();
        context.moveTo(source.x, source.y);
        context.lineTo(target.x, target.y);
        context.stroke();
      }

      for (const node of simNodes) {
        const meta = nodeByStem.get(node.stem);
        if (!meta) continue;
        context.beginPath();
        context.fillStyle = colorForKind(meta.kind);
        context.arc(node.x, node.y, NODE_RADIUS, 0, Math.PI * 2);
        context.fill();
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
    const hitRadius = NODE_RADIUS + 3;
    for (const node of simulationNodesRef.current.values()) {
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
    if (!drag) return;
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

  return (
    <canvas
      ref={canvasRef}
      className="vault-graph-canvas"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onWheel={handleWheel}
    />
  );
}
