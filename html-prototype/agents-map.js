/*
  Second Brain — Agents Map (BUG-002 fix, Option D semantic zoom/drill-down).
  Ported from html-prototype/agents-map-exploration.html's accepted Option D
  + both operator-approved refinements (Hub-sizing rebalance in the
  drill-down view, overview entrance animation) — see REVIEW-QUEUE.md's
  "BUG-002 layout exploration" entry for the full comparison/approval
  history, and agents-map.html's own top-of-file breadcrumb for what changed
  in the markup itself.

  This is the CANONICAL agents-map.html's own page-scoped companion script
  (parallel to app.js, loaded after it), NOT the exploration sandbox's own
  agents-map-exploration.js. The two differ in one important way: the
  exploration computed Hub/agent geometry live from a dataset (so it could
  compare multiple layout options side by side against two different
  scales). This screen's Hub/agent positions are already present in the
  static markup (hand-computed, same convention as every prior revision of
  this file) — so this script only needs to (a) wire click-a-Hub-to-zoom
  interactivity between each state's already-rendered overview and its
  already-rendered per-Section drill-down views, and (b) play the entrance
  animation by capturing/flattening/restoring already-known positions, not
  laying out geometry from a dataset.

  Two behaviors, one per top-level Agents Map state ("Populated",
  "5 sections", "Dense section" — not "First run", which has no agents):

  1. Click-a-Hub-to-zoom drill-down. Each state's own [data-agents-stage-root]
     wraps exactly one [data-agents-overview-stage] (the ordinary polar-grid
     canvas) and one .explore-drilldown (a set of per-Section "Agents Tree"
     views, one active at a time via the existing generic [data-state-panel]
     convention, scoped by its own data-group so multiple states' drill-downs
     never collide). Clicking a .hub-node[data-section-id] button in the
     overview zooms it out (.explore-zoom-overview + .zooming-out, reused
     verbatim from the exploration's own additive styles.css section), then
     swaps to the matching drill-down panel. Each drill-down panel's own
     "Back to Agents Map" button (data-role="agents-drilldown-back")
     reverses it.

  2. Entrance animation (agents-map-exploration.js's playIntro(), ported).
     Plays once for the initially-active top-level state on page load, and
     again whenever the human uses the main state-switcher to enter a
     different agents-having state (a fresh "on load of this view" moment) —
     resetting any left-open drill-down back to the overview first. Also
     replayable on demand via each state's own "Replay intro" button
     (data-agents-replay-intro).
*/

(function () {
  'use strict';

  const INTRO_HOLD_MS = 900; // matches agents-map-exploration.js's own INTRO_HOLD_MS
  const INTRO_MOVE_MS = 900; // matches agents-map-exploration.js's own INTRO_MOVE_MS

  function fmt(n) { return n.toFixed(2); }

  /** Wires click-a-Hub-to-zoom-into-drill-down for one top-level Agents Map
   * state (e.g. "Populated", "5 sections", "Dense section"). `stageRoot` is
   * that state's own [data-agents-stage-root] wrapper, containing exactly
   * one [data-agents-overview-stage] and one .explore-drilldown. */
  function wireDrilldown(stageRoot) {
    const overviewStage = stageRoot.querySelector('[data-agents-overview-stage]');
    const overviewCanvas = stageRoot.querySelector('.agents-map-canvas.explore-zoom-overview');
    const drilldown = stageRoot.querySelector('[data-agents-drilldown]');
    if (!overviewStage || !overviewCanvas || !drilldown) return;

    function showSection(sectionId) {
      drilldown.querySelectorAll('[data-state-panel]').forEach((panel) => {
        panel.classList.toggle('active', panel.dataset.state === sectionId);
      });
    }

    function zoomIn(sectionId) {
      showSection(sectionId);
      overviewCanvas.classList.add('zooming-out');
      const onEnd = () => {
        overviewCanvas.removeEventListener('transitionend', onEnd);
        overviewStage.style.display = 'none';
        drilldown.classList.add('active');
      };
      overviewCanvas.addEventListener('transitionend', onEnd, { once: true });
    }

    function zoomOut() {
      drilldown.classList.remove('active');
      overviewStage.style.display = '';
      overviewCanvas.classList.remove('zooming-out');
    }

    // REQ-SB-38 (Agents Map Density Clustering): a .map-overflow-marker
    // cluster button uses the identical [data-section-id] -> drill-down-panel
    // contract a .hub-node button already uses — it just points at a
    // narrower panel (the clustered subset, not the whole Section) via its
    // own distinct data-section-id value (e.g. "technical-cluster-overflow"
    // vs the real Section's own "technical"). No new interaction code
    // needed, only a wider selector — the same click-to-zoom mechanic BUG-002's
    // Option D established for Hubs, reused one level deeper.
    overviewCanvas.querySelectorAll('.hub-node[data-section-id], .map-overflow-marker[data-section-id]').forEach((hubBtn) => {
      hubBtn.addEventListener('click', () => zoomIn(hubBtn.dataset.sectionId));
    });
    drilldown.querySelectorAll('[data-role="agents-drilldown-back"]').forEach((backBtn) => {
      backBtn.addEventListener('click', zoomOut);
    });

    // Exposed so the DOMContentLoaded wiring below can reset a state's
    // drill-down back to the overview when re-entering it via the main
    // state-switcher, without re-querying these elements a second time.
    stageRoot.__agentsMapZoomOut = zoomOut;
  }

  /** Plays (or replays) the overview entrance animation for one state's
   * overview stage: every agent dot first renders in one flat row (KB/Hubs/
   * rings/spokes/boundary/Section titles all invisible), holds, then glides
   * to its real, already-known polar position while the KB grows/fades in
   * and everything else fades in alongside it. Ported from
   * agents-map-exploration.js's playIntro() — the only difference is
   * positions are already present in this screen's static markup (nothing
   * to compute), so this only captures and temporarily overwrites them. */
  function playIntro(overviewStage) {
    const agentNodes = Array.from(overviewStage.querySelectorAll('.agent-node'));
    // REQ-SB-38: .map-overflow-marker is a structural node like .hub-node
    // (fixed, not an individual agent flattening into the intro row), so it
    // gets the same delayed-fade-in / non-interactive-while-animating
    // treatment as every Hub, not the flat-row-then-glide treatment below.
    const hubNodes = Array.from(overviewStage.querySelectorAll('.hub-node, .map-overflow-marker'));
    const kbNode = overviewStage.querySelector('.kb-node');
    const linesSvg = overviewStage.querySelector('.agents-map-lines');
    const sectionTitles = Array.from(overviewStage.querySelectorAll('.section-title'));
    if (!agentNodes.length) return;

    // Capture each agent's real, already-computed final position before overwriting it below.
    const finalPositions = agentNodes.map((node) => ({ top: node.style.top, left: node.style.left }));

    // Step 1: flat row. Evenly spaced across a wide central band, in DOM
    // order (matches each state's own Section iteration order).
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
    void overviewStage.offsetWidth;

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

  function activeAgentsMapStageRoot() {
    const activePanel = document.querySelector('[data-state-panel][data-group="agents-map"].active');
    return activePanel ? activePanel.querySelector('[data-agents-stage-root]') : null;
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-agents-stage-root]').forEach((stageRoot) => {
      wireDrilldown(stageRoot);

      const replayBtn = stageRoot.querySelector('[data-agents-replay-intro]');
      const overviewStage = stageRoot.querySelector('[data-agents-overview-stage]');
      if (replayBtn && overviewStage) {
        replayBtn.addEventListener('click', () => playIntro(overviewStage));
      }
    });

    // Auto-play the entrance animation once for whichever top-level Agents
    // Map state is active on load (default: "Populated").
    const initialStageRoot = activeAgentsMapStageRoot();
    if (initialStageRoot) {
      const overviewStage = initialStageRoot.querySelector('[data-agents-overview-stage]');
      if (overviewStage) playIntro(overviewStage);
    }

    // Replay it again whenever the human switches into a different
    // agents-having state via the main state-switcher — a fresh "on load of
    // this view" moment — resetting any left-open drill-down back to the
    // overview first. Runs after app.js's own listener on the same buttons
    // has already flipped `.active` on the matching [data-state-panel]:
    // both listeners are attached to the same click event, and app.js's own
    // <script> tag loads (and so registers its DOMContentLoaded handler)
    // before this file's, so its listener is attached first and therefore
    // runs first when the button is later clicked.
    document.querySelectorAll('.state-switcher[data-group="agents-map"] button[data-state-target]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const stageRoot = activeAgentsMapStageRoot();
        if (!stageRoot) return; // "First run" has no [data-agents-stage-root] — nothing to animate
        if (stageRoot.__agentsMapZoomOut) stageRoot.__agentsMapZoomOut();
        const overviewStage = stageRoot.querySelector('[data-agents-overview-stage]');
        if (overviewStage) playIntro(overviewStage);
      });
    });
  });
})();
