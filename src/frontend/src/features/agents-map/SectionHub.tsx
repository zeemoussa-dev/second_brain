import type { CSSProperties } from 'react';
import type { AgentSection } from './mockAgents';
import { HUB_RADIUS, polarToCartesian } from './polarLayout';
import { getVisualIconName } from './visualOptions';

interface SectionHubProps {
  section: AgentSection;
  // Overview call site only: opens this Section's drill-down. Omitted at
  // the drill-down's own call site (SectionDrilldown.tsx), where the Hub
  // stays a plain non-interactive element, matching today's behavior.
  onActivate?: () => void;
  // Drill-down call site only: places the Hub at the drill-down canvas's
  // own literal center (pass 0) instead of the overview's HUB_RADIUS
  // position — mirrors AgentNode's own radiusOverride prop (T03).
  radiusOverride?: number;
  // Overview "Section rotation" wheel (ported from html-prototype's own
  // #skillmapRotor) — a base offset added to the Section's stored
  // hubAngleDeg so the whole ring of Hubs can turn without mutating the
  // underlying layout data. Undefined/0 at every other call site.
  angleOffsetDeg?: number;
  // Overview hover-dim (ported from html-prototype's own .skillmap-tree
  // .dimmed) — true when a DIFFERENT Section is currently hovered.
  dimmed?: boolean;
  // True when THIS Section is the currently-hovered one — drives the
  // Hub's own zoom/glow via a real class instead of CSS :hover (operator,
  // 2026-08-15: "Titles Zooming in but the Sections are not"). The
  // Section-wide hover-wedge (AgentsMapCanvas.tsx, "the Section Hover is
  // the whole Area between the Hub and the Title") sets the SAME shared
  // hoveredSectionId state the title's own `.is-hovered` class already
  // reads, but it's a structurally unrelated SVG element elsewhere in the
  // DOM — CSS :hover / the `.hub-hit-region:hover ~ .hub-node` sibling
  // trick only ever fires from a literal cursor-over-hub(-hit-region), so
  // hovering anywhere else in the wedge zoomed the title (state-driven)
  // but left the Hub itself unzoomed (CSS-hover-driven). This prop makes
  // the Hub react to the exact same state the title does.
  isHovered?: boolean;
  // Overview hover-dim — reports hover enter/leave on the Hub itself AND
  // the oversized hit-region below so AgentsMapCanvas can drive one shared
  // hoveredSectionId. Omitted at the drill-down call site.
  onHoverChange?: (hovering: boolean) => void;
  // Section View drill-down only (operator, 2026-08-28: "the Hub Node...
  // should be 2.5x bigger" than the Agents around it there) — applies
  // `.hub-node--large` (agents-map.css). Omitted (false) at every other
  // call site, matching `.agent-node`'s own identical `large` prop shape.
  large?: boolean;
}

export function SectionHub({
  section,
  onActivate,
  radiusOverride,
  angleOffsetDeg,
  dimmed,
  isHovered,
  onHoverChange,
  large,
}: SectionHubProps) {
  const radius = radiusOverride ?? HUB_RADIUS;
  const angle = section.hubAngleDeg + (angleOffsetDeg ?? 0);
  const { x, y } = polarToCartesian(radius, angle);
  // Every Section carries its own color/icon now (operator, 2026-08-15:
  // "every section Should have its own Color and Icon, The Hub should
  // Match the Color of the Section") — `--hub-color` is what
  // agents-map.css's own `.hub-node`/`.hub-node-icon`/hover-glow rules
  // already read (falling back to --color-accent when a Section has
  // none set), so setting it here is the only wiring needed; the icon
  // glyph falls back to the generic "hub" glyph the same way.
  const style: CSSProperties = { top: `${y}%`, left: `${x}%` };
  if (section.color) style['--hub-color' as string] = section.color;
  // Same picker-id -> real-ligature resolution AgentNode.tsx already
  // applies (2026-08-16, "icons still not visible on agents") -- a
  // Section's own icon can be a VisualPicker `id` (e.g. "compass") whose
  // real Material Symbols ligature differs ("explore"); rendering the id
  // directly renders the literal word instead of substituting the glyph.
  // SectionHub never got this same fix, so any Section using one of the
  // handful of id!=ligature entries (VISUAL_ICONS in visualOptions.ts)
  // showed unreadable text instead of its icon -- both here (overview)
  // and in SectionDrilldown.tsx, which renders this same component.
  const iconGlyph = getVisualIconName(section.icon) ?? 'hub';

  if (onActivate) {
    return (
      <>
        {/* Oversized invisible click/hover target (ported from
            html-prototype's own .skillmap-tree-hit — "Section is the Full
            Area not the Hub"). Shares the Hub's own position/onActivate;
            no explicit z-index so it stacks BELOW .hub-node's z-index:2,
            meaning a direct click on the small visible Hub icon still
            resolves to the Hub itself, while the surrounding empty ring
            around it now also enters the Section. */}
        <button
          type="button"
          className="hub-hit-region"
          style={style}
          aria-hidden="true"
          tabIndex={-1}
          onClick={onActivate}
          onMouseEnter={() => onHoverChange?.(true)}
          onMouseLeave={() => onHoverChange?.(false)}
        />
        <button
          type="button"
          className={`hub-node${large ? ' hub-node--large' : ''}${dimmed ? ' is-dimmed' : ''}${isHovered ? ' is-hovered' : ''}`}
          style={style}
          data-section-id={section.id}
          aria-label={section.hubLabel}
          title={section.hubLabel}
          onClick={onActivate}
          onMouseEnter={() => onHoverChange?.(true)}
          onMouseLeave={() => onHoverChange?.(false)}
        >
          {/* Icon, not text (operator, 2026-08-15: "Replace the Hub Text
              with an Icon") — the Section's own icon, falling back to a
              generic "hub" glyph if it has none set. `hubLabel` moves to
              aria-label/title above so the real name is still available
              to assistive tech and on hover, not lost. */}
          <span className="material-symbols-outlined hub-node-icon" aria-hidden="true">{iconGlyph}</span>
        </button>
      </>
    );
  }

  return (
    <div className={`hub-node${large ? ' hub-node--large' : ''}`} style={style} aria-label={section.hubLabel} title={section.hubLabel}>
      <span className="material-symbols-outlined hub-node-icon" aria-hidden="true">{iconGlyph}</span>
    </div>
  );
}
