/*
  Second Brain — Agents Map layout exploration (BUG-002: sections with 4+
  agents visually spill into neighboring sections' territory, labels
  collide). Computes and renders 4 candidate fixes directly in JS against
  two real datasets — today's real 5-agent/5-section state (identical to
  the already-approved "5 sections" reference in agents-map.html) and a
  synthetic 13-agent/6-section stress case — so geometry is live-computed,
  not hand-placed percentages (this exploration's own point: hand-placing
  ~8 divergent layouts by hand would repeat exactly the "6 rounds of manual
  re-derivation" pain agents-map.html's own revision history documents).

  Ported constants/formula match the REAL production code exactly:
  CENTER/RING_RADIUS/HUB_RADIUS/BOUNDARY_RADIUS/polarToCartesian from
  src/frontend/src/features/agents-map/polarLayout.ts; the section-divider
  midpoint-angle formula from AgentsMapCanvas.tsx. Options A/C/D's dynamic
  angular-budget formula is a direct generalization of layoutAgents.ts's
  existing SECTION_ARC_SPAN_DEG mechanism (this is literally BUG-002's root
  cause, made N-aware) — not a new geometric idea, a fix to the existing one.

  Exploration-only simplifications (NOT carried into the winning option when
  it's merged back into agents-map.html): the Knowledge Base renders as a
  plain accent circle instead of the full 23-neuron brain mesh, and the
  PRODUCER/EXPERT/WORKER ring-label text is omitted — both are ambient
  decoration unrelated to the angular-collision problem under comparison.

  ---------------------------------------------------------------------------
  Operator sign-off pass (2026-08-11): the operator picked Option D
  (semantic zoom / drill-down) as the accepted direction — it is no longer
  one of four alternatives being compared, it is the base being refined.
  Options A/B/C below are kept AS-IS (comparison history, not being
  iterated further). Two concrete refinements were requested against Option
  D specifically:

    1. Hub-sizing rebalance in the drill-down "Agents Tree" view — see
       styles.css's `.explore-drilldown .hub-node` rule and its own
       breadcrumb for the before/after numbers. Pure CSS, no JS change.
    2. A replayable overview entrance animation (`playIntro()` below, wired
       to the new "Entrance animation" card inside Option D's own section)
       — flat row -> hold -> transition into real polar/circular positions,
       with the Knowledge Base growing/fading in at center. See
       `playIntro()`'s own header comment for the exact mechanics and
       styles.css's matching breadcrumb for the CSS side.

  Neither refinement is approved yet — this pass only builds them for
  browser review; see REVIEW-QUEUE.md's updated BUG-002 entry.
  ---------------------------------------------------------------------------
*/

(function () {
  'use strict';

  // ---- Shared geometry (ported from polarLayout.ts / AgentsMapCanvas.tsx) -

  const CENTER = 50;
  const RING_RADIUS = { producer: 30, expert: 45, worker: 50 };
  const HUB_RADIUS = 32;
  const BOUNDARY_RADIUS = 58;
  const SECTION_BOUNDARY_INNER_RADIUS = 18;
  const SPOKE_LENGTH = 108;
  // Above this natural extent, uniformly compress the whole render so it
  // still fits the canvas — only ever kicks in for Option B, whose radial
  // stacking can push a crowded section's own agents well past the shared
  // rings. A/C/D never approach this ceiling with either dataset below.
  const SCALE_CEILING = 90;

  function polar(radius, angleDeg) {
    const rad = (angleDeg * Math.PI) / 180;
    return { x: CENTER + radius * Math.cos(rad), y: CENTER + radius * Math.sin(rad) };
  }

  function keywordList(agent) {
    return (agent.keywords || '')
      .split(',')
      .map((k) => k.trim().toLowerCase())
      .filter(Boolean);
  }

  // Exact shared-term count between two agents' free-text Keywords
  // (REQ-SB-20). A stand-in for REQ-SB-20's own real routing-relevance
  // scoring, which doesn't exist yet — this is enough to demonstrate the
  // *visual outcome* (closer affinity -> closer placement / a drawn
  // relationship), not a claim about what the real Hub routing algorithm
  // will compute.
  function overlapScore(a, b) {
    const bList = keywordList(b);
    return keywordList(a).filter((k) => bList.includes(k)).length;
  }

  // Greedy nearest-neighbor chain by keyword overlap — approximates "closer
  // affinity sits closer together" without a real force-directed physics
  // simulation (out of scope for a static HTML/CSS/JS prototype with no
  // build step). Good enough to prove the visual idea; a real
  // implementation would want an actual layout algorithm.
  function orderByAffinity(agents) {
    if (agents.length <= 2) return agents.slice();
    const remaining = agents.slice();
    const chain = [remaining.shift()];
    while (remaining.length) {
      const last = chain[chain.length - 1];
      remaining.sort((a, b) => overlapScore(last, b) - overlapScore(last, a));
      chain.push(remaining.shift());
    }
    return chain;
  }

  // ---- Layout algorithms ---------------------------------------------------

  const FAN_FRACTION = 0.8; // agents fan across 80% of the section's TRUE wedge (360/N), never a fixed constant
  const COMPACT_THRESHOLD = 3; // >3 agents in one section -> fall back to the existing (already-styled, previously unused) compact/hover-label node

  // Option A (also the base for Option D's overview) and Option C (adds
  // affinity-based reordering) share this one function.
  function layoutDynamicWedge(sections, { forceCompact = false, reorderByAffinity = false } = {}) {
    const n = sections.length;
    const wedge = 360 / n;
    return sections.map((section, i) => {
      const hubAngle = i * wedge - 90;
      const span = wedge * FAN_FRACTION;
      const orderedAgents = reorderByAffinity ? orderByAffinity(section.agents) : section.agents;
      const compact = forceCompact || orderedAgents.length > COMPACT_THRESHOLD;
      const agents = orderedAgents.map((agent, idx) => {
        const offset = orderedAgents.length <= 1 ? 0 : (idx / (orderedAgents.length - 1) - 0.5) * span;
        return Object.assign({}, agent, { angle: hubAngle + offset, radius: RING_RADIUS[agent.type], compact: compact });
      });
      return Object.assign({}, section, { hubAngle: hubAngle, agents: agents, boundaryRadius: BOUNDARY_RADIUS });
    });
  }

  function layoutAffinityCluster(sections) {
    return layoutDynamicWedge(sections, { reorderByAffinity: true });
  }

  function layoutOverviewCompact(sections) {
    return layoutDynamicWedge(sections, { forceCompact: true });
  }

  // Option B: agents stay within a narrow, fixed angular sliver (never wider
  // than NARROW_SPAN_CAP, and always a fraction of the true wedge too, so it
  // shrinks further for very high N) regardless of how many share the
  // section — density is absorbed by RADIAL stacking within the same Type's
  // ring instead. Guarantees zero angular spillover by construction; the
  // section's own outer radius (and, here, the shared boundary that's sized
  // to fit the worst section) grows instead.
  const NARROW_SPAN_CAP = 20;
  const SPAN_FRACTION = 0.35;
  const STACK_STEP = 12; // >= a regular agent-node's own ~10-unit diameter, so stacked nodes never overlap radially

  function layoutStackedWedge(sections) {
    const n = sections.length;
    const wedge = 360 / n;
    let maxRadius = BOUNDARY_RADIUS;
    const laidOut = sections.map((section, i) => {
      const hubAngle = i * wedge - 90;
      const span = Math.min(NARROW_SPAN_CAP, wedge * SPAN_FRACTION);
      const typeCounts = {};
      const agents = section.agents.map((agent, idx) => {
        const offset = section.agents.length <= 1 ? 0 : (idx / (section.agents.length - 1) - 0.5) * span;
        const stackIndex = typeCounts[agent.type] || 0;
        typeCounts[agent.type] = stackIndex + 1;
        const radius = RING_RADIUS[agent.type] + stackIndex * STACK_STEP;
        maxRadius = Math.max(maxRadius, radius);
        return Object.assign({}, agent, { angle: hubAngle + offset, radius: radius, compact: false });
      });
      return Object.assign({}, section, { hubAngle: hubAngle, agents: agents });
    });
    const boundaryRadius = maxRadius + 8;
    laidOut.forEach((s) => { s.boundaryRadius = boundaryRadius; });
    return laidOut;
  }

  // ---- Rendering ------------------------------------------------------------

  function sectionDividerAngles(sections) {
    const angles = sections.map((s) => s.hubAngle).slice().sort((a, b) => a - b);
    return sections.map((s) => {
      const idx = angles.indexOf(s.hubAngle);
      const next = idx + 1 < angles.length ? angles[idx + 1] : angles[0] + 360;
      return (angles[idx] + next) / 2;
    });
  }

  function fmt(n) { return n.toFixed(2); }

  /** Renders one overview canvas (Options A/B/C, and D's own overview state)
   * into `mountEl`. `hubClickable` (Option D only) renders each Hub as a
   * real <button> wired for click-to-zoom instead of the ordinary
   * non-clickable <div> every other option (and the canonical
   * agents-map.html) uses. */
  function render(mountEl, sections, options) {
    options = options || {};
    const showAffinity = !!options.showAffinity;
    const hubClickable = !!options.hubClickable;

    const naturalMax = Math.max.apply(null, [BOUNDARY_RADIUS].concat(
      sections.map((s) => s.boundaryRadius || BOUNDARY_RADIUS),
      sections.reduce((acc, s) => acc.concat(s.agents.map((a) => a.radius)), []),
    ));
    const scale = naturalMax > SCALE_CEILING ? SCALE_CEILING / naturalMax : 1;
    const dividerAngles = sectionDividerAngles(sections);

    let svg = '';
    for (let deg = 0; deg < 360; deg += 30) {
      const p = polar(SPOKE_LENGTH * scale, deg);
      svg += '<line class="radar-spoke" x1="50" y1="50" x2="' + fmt(p.x) + '" y2="' + fmt(p.y) + '" />';
    }
    ['producer', 'expert', 'worker'].forEach((type) => {
      svg += '<circle class="ring-circle" cx="50" cy="50" r="' + fmt(RING_RADIUS[type] * scale) + '" />';
    });

    sections.forEach((section, i) => {
      const boundaryR = (section.boundaryRadius || BOUNDARY_RADIUS) * scale;
      svg += '<circle class="boundary-circle" cx="50" cy="50" r="' + fmt(boundaryR) + '" />';
      const mid = dividerAngles[i];
      const inner = polar(SECTION_BOUNDARY_INNER_RADIUS * scale, mid);
      const outer = polar(boundaryR, mid);
      svg += '<line class="section-boundary" x1="' + fmt(inner.x) + '" y1="' + fmt(inner.y) + '" x2="' + fmt(outer.x) + '" y2="' + fmt(outer.y) + '" />';
      const hubPoint = polar(HUB_RADIUS * scale, section.hubAngle);
      svg += '<line class="spoke-line" x1="50" y1="50" x2="' + fmt(hubPoint.x) + '" y2="' + fmt(hubPoint.y) + '" stroke="var(--color-accent)" />';
      section.agents.forEach((agent) => {
        const p = polar(agent.radius * scale, agent.angle);
        svg += '<line class="cluster-line" x1="' + fmt(hubPoint.x) + '" y1="' + fmt(hubPoint.y) + '" x2="' + fmt(p.x) + '" y2="' + fmt(p.y) + '" stroke="var(--color-accent)" />';
      });
    });

    if (showAffinity) {
      const allAgents = [];
      sections.forEach((s) => {
        s.agents.forEach((a) => {
          allAgents.push(Object.assign({}, a, { sectionId: s.id, hubAngle: s.hubAngle }));
        });
      });
      for (let i = 0; i < allAgents.length; i += 1) {
        for (let j = i + 1; j < allAgents.length; j += 1) {
          const a = allAgents[i];
          const b = allAgents[j];
          if (a.sectionId === b.sectionId) continue;
          if (overlapScore(a, b) === 0) continue;
          const pa = polar(a.radius * scale, a.angle);
          const pb = polar(b.radius * scale, b.angle);
          const hubA = polar(HUB_RADIUS * scale, a.hubAngle);
          const hubB = polar(HUB_RADIUS * scale, b.hubAngle);
          const points = [pa, hubA, hubB, pb].map((p) => fmt(p.x) + ',' + fmt(p.y)).join(' ');
          svg += '<polyline class="affinity-line" data-agents="|' + a.id + '|' + b.id + '|" points="' + points + '" />';
        }
      }
    }

    let nodesHtml = '<div class="kb-node" style="animation:none;"><span class="kb-node-label">Knowledge Base</span></div>';
    sections.forEach((section, i) => {
      const hubPoint = polar(HUB_RADIUS * scale, section.hubAngle);
      const hubTag = hubClickable ? 'button' : 'div';
      const hubAttrs = hubClickable
        ? 'type="button" class="hub-node" data-section-id="' + section.id + '"'
        : 'class="hub-node"';
      const count = section.agents.length;
      nodesHtml += '<' + hubTag + ' ' + hubAttrs + ' style="top:' + fmt(hubPoint.y) + '%; left:' + fmt(hubPoint.x) + '%;">'
        + section.name + ' Hub<span class="hub-node-type">' + count + ' agent' + (count === 1 ? '' : 's') + (count === 0 ? ' — empty' : '') + (hubClickable ? ' · click to zoom in' : '') + '</span></' + hubTag + '>';

      section.agents.forEach((agent) => {
        const p = polar(agent.radius * scale, agent.angle);
        const compactClass = agent.compact ? ' agent-node--compact' : '';
        const fixtureNote = agent.fixture ? ' <span class="text-muted">(illustrative)</span>' : '';
        nodesHtml += '<button type="button" class="agent-node agent-node--' + agent.type + compactClass + '" style="top:' + fmt(p.y) + '%; left:' + fmt(p.x) + '%;" data-agent-id="' + agent.id + '">'
          + '<span class="agent-node-label">' + agent.label + fixtureNote + '</span><span class="agent-node-type">' + agent.type + '</span></button>';
      });

      const titleR = (section.boundaryRadius || BOUNDARY_RADIUS) * scale + 8 + (i % 2 === 0 ? 0 : 8);
      const titlePoint = polar(titleR, section.hubAngle);
      const illustrativeNote = section.illustrative
        ? ' <span class="text-muted" style="font-weight:400; letter-spacing:normal; text-transform:none;">(illustrative)</span>'
        : '';
      nodesHtml += '<div class="section-title" style="top:' + fmt(titlePoint.y) + '%; left:' + fmt(titlePoint.x) + '%;">'
        + section.name + illustrativeNote + '<span class="section-title-accent" style="background: var(--color-accent);"></span></div>';
    });

    mountEl.innerHTML = '<svg class="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">' + svg + '</svg>' + nodesHtml;

    if (showAffinity) {
      mountEl.querySelectorAll('.agent-node').forEach((node) => {
        const id = node.dataset.agentId;
        const on = () => highlightAffinity(mountEl, id, true);
        const off = () => highlightAffinity(mountEl, id, false);
        node.addEventListener('mouseover', on);
        node.addEventListener('mouseout', off);
        node.addEventListener('focus', on);
        node.addEventListener('blur', off);
      });
    }
  }

  function highlightAffinity(mountEl, agentId, on) {
    mountEl.querySelectorAll('.affinity-line[data-agents*="|' + agentId + '|"]').forEach((line) => {
      line.classList.toggle('active', on);
    });
  }

  /** Renders one Section's full "Agents Tree" drill-down view (Option D) —
   * the Section's own agents spread across the FULL 360deg instead of a
   * thin wedge, since this view no longer has to share the canvas with any
   * other Section; direct (not Hub-routed) affinity lines between agents
   * that share a keyword, always shown (no hover-gating needed — far fewer
   * candidate pairs once scoped to one Section). */
  function renderSectionTree(container, section, backLabel) {
    const agents = section.agents;
    const n = agents.length;
    const radius = 40;
    const positioned = agents.map((agent, idx) => {
      const angle = n === 0 ? 0 : (idx / n) * 360 - 90;
      return Object.assign({}, agent, { angle: angle, radius: radius });
    });

    let svg = '';
    positioned.forEach((agent) => {
      const p = polar(agent.radius, agent.angle);
      svg += '<line class="cluster-line" x1="50" y1="50" x2="' + fmt(p.x) + '" y2="' + fmt(p.y) + '" stroke="var(--color-accent)" />';
    });
    for (let i = 0; i < positioned.length; i += 1) {
      for (let j = i + 1; j < positioned.length; j += 1) {
        if (overlapScore(positioned[i], positioned[j]) === 0) continue;
        const pa = polar(positioned[i].radius, positioned[i].angle);
        const pb = polar(positioned[j].radius, positioned[j].angle);
        svg += '<line class="affinity-line active" x1="' + fmt(pa.x) + '" y1="' + fmt(pa.y) + '" x2="' + fmt(pb.x) + '" y2="' + fmt(pb.y) + '" />';
      }
    }

    let nodesHtml = '<div class="hub-node" style="top:50%; left:50%;">' + section.name + ' Hub<span class="hub-node-type">' + n + ' agent' + (n === 1 ? '' : 's') + '</span></div>';
    positioned.forEach((agent) => {
      const p = polar(agent.radius, agent.angle);
      const fixtureNote = agent.fixture ? ' <span class="text-muted">(illustrative)</span>' : '';
      nodesHtml += '<button type="button" class="agent-node agent-node--' + agent.type + '" style="top:' + fmt(p.y) + '%; left:' + fmt(p.x) + '%;" data-agent-id="' + agent.id + '">'
        + '<span class="agent-node-label">' + agent.label + fixtureNote + '</span><span class="agent-node-type">' + agent.type + '</span></button>';
    });

    container.innerHTML = '<button type="button" class="btn" data-role="explore-back">← ' + backLabel + '</button>'
      + '<div class="agents-map-stage"><div class="agents-map-canvas">'
      + '<svg class="agents-map-lines" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">' + svg + '</svg>'
      + nodesHtml
      + '</div></div>'
      + (n === 0 ? '<div class="empty-state"><p class="text-muted">No agents in this Section yet — a real, buildable empty Section (REQ-SB-18 Scenario 7), same as the overview.</p></div>' : '')
      + '<p class="text-muted" style="margin-top: var(--space-3);">Direct agent-to-agent lines here (not Hub-routed) are illustrative only — REQ-SB-20\'s own Notes leave within-Section routing an open question for /spec; this view assumes it may be simpler than cross-Section routing, not a decided answer.</p>';
  }

  /** Wires click-to-zoom on every clickable Hub inside one Option-D overview
   * mount: a CSS transform/opacity transition on the overview stage, then
   * (on transitionend) a state-swap to the per-Section drill-down view. */
  function wireDrilldown(stageRoot, overviewMount, sections) {
    overviewMount.querySelectorAll('.hub-node[data-section-id]').forEach((hubBtn) => {
      hubBtn.addEventListener('click', () => {
        const section = sections.find((s) => s.id === hubBtn.dataset.sectionId);
        const overviewStage = stageRoot.querySelector('[data-explore-overview-stage]');
        const drilldown = stageRoot.querySelector('[data-explore-drilldown]');
        overviewMount.classList.add('explore-zoom-overview');
        // Force layout so the class above is applied before zooming-out is added (transition needs a starting frame).
        void overviewMount.offsetWidth;
        overviewMount.classList.add('zooming-out');

        const onEnd = () => {
          overviewMount.removeEventListener('transitionend', onEnd);
          overviewStage.style.display = 'none';
          drilldown.classList.add('active');
          renderSectionTree(drilldown.querySelector('[data-explore-tree-mount]'), section, 'Back to Agents Map');
          const backBtn = drilldown.querySelector('[data-role="explore-back"]');
          if (backBtn) {
            backBtn.addEventListener('click', () => {
              drilldown.classList.remove('active');
              overviewStage.style.display = '';
              overviewMount.classList.remove('zooming-out');
            });
          }
        };
        overviewMount.addEventListener('transitionend', onEnd, { once: true });
      });
    });
  }

  // ---- Refinement 2: overview entrance animation (operator sign-off pass) -

  const INTRO_HOLD_MS = 900; // how long the flat "next to each other" row holds before it moves — long enough to actually read, short enough to still feel like "a quick scroll"
  const INTRO_MOVE_MS = 900; // duration of the flat -> circular transition itself

  /** Renders one Option-D overview into `mountEl` (reusing the existing
   * `render()` — same DOM, same final polar positions, same click-to-zoom
   * wiring) and then plays the entrance sequence over it:
   *   1. FLAT — every agent dot is repositioned to one flat, evenly-spaced
   *      row (same y, spread x) instead of its real polar slot; the KB,
   *      every Hub, and the rings/spokes/boundary/Section titles all start
   *      invisible. This is the literal starting frame — no animation has
   *      played yet, so a reviewer opening the page or clicking "Replay
   *      intro" sees the flat row FIRST, not a flash of the final circle.
   *   2. HOLD — a `INTRO_HOLD_MS` pause with nothing moving, so the flat
   *      row is clearly legible as "agents next to each other" before step 3.
   *   3. TRANSITION — every agent's top/left is set back to its real,
   *      already-known circular position (captured from `render()`'s own
   *      output before step 1 overwrote it) while `.agent-node--intro-move`
   *      is attached, so the browser CSS-transitions the move over
   *      `INTRO_MOVE_MS`. In the exact same instant: the KB's `animation`
   *      is set to `kbGrowIn` (opacity/scale grow-in) layered with the
   *      existing looping `kbPulse`, and every Hub's existing `nodeFadeIn`
   *      (already on `.hub-node` by default, `backwards` fill-mode) was
   *      given `animation-delay: INTRO_HOLD_MS` back in step 1 — so it
   *      simply fires on schedule here, no second trigger needed — and the
   *      rings/spokes/boundary/Section titles fade in via their own
   *      `agents-intro-fade` class being removed.
   *   4. SETTLED — `agent-node--intro-move` and the `pointer-events: none`
   *      guard on the Hubs (kept non-clickable while still animating in)
   *      are cleared, leaving an ordinary, fully-interactive Option-D
   *      overview — identical to a normal (non-intro) render.
   */
  function playIntro(mountEl, sections) {
    // hubClickable: false — this demo is scoped to the entrance sequence
    // only (see wireIntroDemo's own comment); rendering clickable Hubs with
    // no click handler wired would be a dead, misleading affordance
    // ("click to zoom in" text + pointer cursor that does nothing here).
    render(mountEl, sections, { hubClickable: false });

    const agentNodes = Array.from(mountEl.querySelectorAll('.agent-node'));
    const hubNodes = Array.from(mountEl.querySelectorAll('.hub-node'));
    const kbNode = mountEl.querySelector('.kb-node');
    const linesSvg = mountEl.querySelector('.agents-map-lines');
    const sectionTitles = Array.from(mountEl.querySelectorAll('.section-title'));

    // Capture each agent's real, already-computed final position before overwriting it below.
    const finalPositions = agentNodes.map((node) => ({ top: node.style.top, left: node.style.left }));

    // Step 1: flat row. Evenly spaced across a wide central band, in DOM
    // order (matches Section iteration order, so it reads left-to-right the
    // same way the map's own Section order does).
    const n = agentNodes.length;
    const marginPct = 12;
    const usablePct = 100 - marginPct * 2;
    agentNodes.forEach((node, idx) => {
      const flatLeft = n <= 1 ? 50 : marginPct + (idx / (n - 1)) * usablePct;
      node.style.top = '50%';
      node.style.left = fmt(flatLeft) + '%';
      node.classList.add('agent-node--intro-move');
    });

    hubNodes.forEach((node) => {
      node.style.animationDelay = INTRO_HOLD_MS + 'ms'; // nodeFadeIn (backwards fill-mode) stays at its 0%-opacity frame until this delay elapses
      node.style.pointerEvents = 'none'; // not clickable while still invisible/animating in
    });
    if (kbNode) {
      kbNode.style.animation = 'kbGrowIn 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) ' + INTRO_HOLD_MS + 'ms both, kbPulse 3s ease-in-out infinite';
    }
    if (linesSvg) linesSvg.classList.add('agents-intro-fade');
    sectionTitles.forEach((title) => title.classList.add('agents-intro-fade'));

    // Force layout so the flat-row starting frame actually paints before anything below moves it.
    void mountEl.offsetWidth;

    window.setTimeout(() => {
      // Step 3: release every agent to its real circular position — the
      // `agent-node--intro-move` transition (added in step 1) animates it.
      agentNodes.forEach((node, idx) => {
        node.style.top = finalPositions[idx].top;
        node.style.left = finalPositions[idx].left;
      });
      if (linesSvg) linesSvg.classList.remove('agents-intro-fade');
      sectionTitles.forEach((title) => title.classList.remove('agents-intro-fade'));
    }, INTRO_HOLD_MS);

    window.setTimeout(() => {
      // Step 4: settled — clean up the intro-only affordances.
      agentNodes.forEach((node) => node.classList.remove('agent-node--intro-move'));
      hubNodes.forEach((node) => { node.style.pointerEvents = ''; });
    }, INTRO_HOLD_MS + INTRO_MOVE_MS + 50);
  }

  /** Wires one "Entrance animation" demo mount: plays the intro once on
   * load (simulating landing on the Agents Map) and re-plays it on demand
   * via its "Replay intro" button. Deliberately does NOT also wire
   * click-to-zoom-into-drilldown on this mount — that mechanic is already
   * demonstrated by the ordinary Option-D overview above; combining both
   * here would conflate two separate refinements in one demo. The same
   * `playIntro()` generalizes trivially to a "replay on Back-to-Agents-Map"
   * trigger too (per the task's own "at minimum cover initial load, your
   * call on covering Back" framing) — not wired here to keep this demo
   * focused on the one thing it's reviewing.
   */
  function wireIntroDemo(mountEl, replayBtn, sections) {
    playIntro(mountEl, sections);
    replayBtn.addEventListener('click', () => playIntro(mountEl, sections));
  }

  // ---- Datasets ---------------------------------------------------------
  // TODAY mirrors the already-approved "5 sections (REQ-SB-18 N-section
  // reference)" state in agents-map.html exactly (same 5 names, same
  // per-section agent counts, same real agent ids/types/keywords already
  // authored in that file's own side panel). STRESS is a synthetic
  // 13-agent/6-section case for testing scale beyond what real data
  // currently provides — every non-real agent/section is marked `fixture`/
  // `illustrative` and called out as such in both the rendered labels and
  // this file's own comments; it is not a proposal to add these agents or
  // a 6th Section for real.

  const TODAY_SECTIONS = [
    { id: 'technical', name: 'Technical', agents: [
      { id: 'vault-qa', label: 'Vault Q&A', type: 'expert', keywords: 'vault search, question answering, knowledge lookup' },
    ] },
    { id: 'sales', name: 'Sales', agents: [] },
    { id: 'productivity', name: 'Productivity', agents: [
      { id: 'email-capture', label: 'Email Capture', type: 'worker', keywords: 'email, inbox, customer correspondence, message classification' },
      { id: 'meeting-capture', label: 'Meeting Capture', type: 'worker', keywords: 'meetings, calendar, scheduling, attendees' },
      { id: 'todo-capture', label: 'To-Do Capture', type: 'worker', keywords: '' },
    ] },
    { id: 'customers', name: 'Customers', agents: [
      { id: 'people-producer', label: 'People Notes', type: 'producer', keywords: 'people, contacts, person notes, attendee bios' },
    ] },
    { id: 'products', name: 'Products', agents: [] },
  ];

  const STRESS_SECTIONS = [
    { id: 'technical', name: 'Technical', agents: [
      { id: 'vault-qa', label: 'Vault Q&A', type: 'expert', keywords: 'vault search, question answering, knowledge lookup' },
      { id: 'log-analyzer', label: 'Log Analyzer', type: 'worker', keywords: 'logs, error analysis, diagnostics', fixture: true },
      { id: 'metrics-bot', label: 'Metrics Bot', type: 'worker', keywords: 'metrics, dashboards, performance', fixture: true },
      { id: 'deploy-watcher', label: 'Deploy Watcher', type: 'producer', keywords: 'deployments, release notes, changelog', fixture: true },
    ] },
    { id: 'sales', name: 'Sales', agents: [
      { id: 'sales-notes', label: 'Sales Notes', type: 'producer', keywords: 'sales notes, pipeline, deal tracking', fixture: true },
    ] },
    { id: 'productivity', name: 'Productivity', agents: [
      { id: 'email-capture', label: 'Email Capture', type: 'worker', keywords: 'email, inbox, customer correspondence, message classification' },
      { id: 'meeting-capture', label: 'Meeting Capture', type: 'worker', keywords: 'meetings, calendar, scheduling, attendees' },
      { id: 'todo-capture', label: 'To-Do Capture', type: 'worker', keywords: '' },
    ] },
    { id: 'customers', name: 'Customers', agents: [
      { id: 'people-producer', label: 'People Notes', type: 'producer', keywords: 'people, contacts, person notes, attendee bios' },
      { id: 'renewal-tracker', label: 'Renewal Tracker', type: 'worker', keywords: 'customer correspondence, contract renewal, renewal tracking', fixture: true },
    ] },
    { id: 'products', name: 'Products', agents: [] },
    { id: 'marketing', name: 'Marketing', illustrative: true, agents: [
      { id: 'content-planner', label: 'Content Planner', type: 'expert', keywords: 'content planning, editorial calendar, changelog', fixture: true },
      { id: 'social-listener', label: 'Social Listener', type: 'worker', keywords: 'social listening, mentions, brand monitoring', fixture: true },
      { id: 'campaign-notes', label: 'Campaign Notes', type: 'producer', keywords: 'campaign notes, marketing content', fixture: true },
    ] },
  ];

  // ---- Wiring -------------------------------------------------------------

  document.addEventListener('DOMContentLoaded', () => {
    const mounts = document.querySelectorAll('[data-explore-mount]');
    mounts.forEach((mount) => {
      const key = mount.dataset.exploreMount; // e.g. "a-today", "c-stress"
      const [optionKey, scaleKey] = key.split('-');
      const dataset = scaleKey === 'today' ? TODAY_SECTIONS : STRESS_SECTIONS;
      let sections;
      let showAffinity = false;
      let hubClickable = false;
      if (optionKey === 'a') {
        sections = layoutDynamicWedge(dataset);
      } else if (optionKey === 'b') {
        sections = layoutStackedWedge(dataset);
      } else if (optionKey === 'c') {
        sections = layoutAffinityCluster(dataset);
        showAffinity = true;
      } else if (optionKey === 'd') {
        sections = layoutOverviewCompact(dataset);
        hubClickable = true;
      } else {
        return;
      }
      render(mount, sections, { showAffinity: showAffinity, hubClickable: hubClickable });

      if (optionKey === 'd') {
        const stageRoot = mount.closest('[data-explore-stage-root]');
        if (stageRoot) wireDrilldown(stageRoot, mount, sections);
      }
    });

    // Refinement 2 — entrance animation demo mounts (Option D overview only).
    document.querySelectorAll('[data-explore-intro-mount]').forEach((mount) => {
      const scaleKey = mount.dataset.exploreIntroMount; // "today" | "stress"
      const dataset = scaleKey === 'today' ? TODAY_SECTIONS : STRESS_SECTIONS;
      const sections = layoutOverviewCompact(dataset);
      const replayBtn = mount.closest('[data-explore-intro-panel]').querySelector('[data-explore-intro-replay]');
      wireIntroDemo(mount, replayBtn, sections);
    });
  });
})();
