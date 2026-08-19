// Agents Map — radial workspace exploration (REQ-SB-52 rebuild pass).
// Page-scoped script, parallel to agents-map.js — this file is NOT wired
// into the canonical screen. Static 3-section/5-agent fixture, same dataset
// agents-map.html's own "Populated" state already established; no fetches,
// no framework, matching this prototype's existing zero-build convention.

(function () {
  // Reference's own real #hub is a 228-circle scattered constellation
  // (confirmed via live DOM inspection: varied radius 0.8-2, several
  // department-tinted color clusters), not a sparse handful of nodes —
  // "not at the many Dots they Have" (operator, 2026-08-14). Generated
  // programmatically (typing 70+ individual SVG elements by hand isn't
  // practical) as an OUTER FIELD around this app's existing connected
  // 7-neuron core (kept, not replaced — it's this project's own established
  // KB mechanic, still pulsing/connected) using a small seeded PRNG so the
  // scatter is deterministic across reloads, not visually different every
  // time. Colored by cycling this app's own real agent-type tokens plus the
  // KB accent — grounded in the actual data model, not arbitrary.
  function renderKbConstellation() {
    const svg = document.querySelector(".kb-brain-svg");
    if (!svg) return;
    const NS = "http://www.w3.org/2000/svg";
    const colors = [
      "var(--agent-color-worker)",
      "var(--agent-color-producer)",
      "var(--agent-color-expert)",
      "var(--sm-accent)",
    ];
    let seed = 1337;
    function rnd() {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    }
    const group = document.createElementNS(NS, "g");
    group.setAttribute("class", "skillmap-kb-constellation");
    // Operator (2026-08-14): "more dots and more clustered in a center" —
    // more dots (140 -> 220) AND biased toward the center: radius uses
    // rnd()^1.7 rather than a flat rnd(), so most dots land close in and
    // progressively fewer reach the outer edge, instead of an even spread
    // across the whole disc.
    for (let i = 0; i < 220; i += 1) {
      const angle = rnd() * Math.PI * 2;
      const radius = 3 + 41 * Math.pow(rnd(), 1.7);
      const cx = 50 + radius * Math.cos(angle);
      const cy = 50 + radius * Math.sin(angle);
      const r = 0.35 + rnd() * 1.0;
      const circle = document.createElementNS(NS, "circle");
      circle.setAttribute("cx", cx.toFixed(1));
      circle.setAttribute("cy", cy.toFixed(1));
      circle.setAttribute("r", r.toFixed(2));
      circle.setAttribute("fill", colors[i % colors.length]);
      circle.setAttribute("opacity", (0.3 + rnd() * 0.4).toFixed(2));
      group.appendChild(circle);
    }
    svg.insertBefore(group, svg.firstChild);
  }
  renderKbConstellation();

  // Hover-rotate that stops IN PLACE (operator, 2026-08-14: "when I remove
  // it don't reset the position just Zoom out and Stop") — a CSS animation
  // gated directly on `:hover` has no way to do this (removing it just
  // reverts to the base style); instead JS toggles `.is-spinning` (see
  // styles.css's own `.skillmap-kb.is-spinning .kb-brain-svg` rule, which
  // has no explicit 0% keyframe so it resumes from whatever `transform`
  // already is) and, on mouseleave, reads the CURRENT computed rotation
  // angle off the animated element and freezes it as a plain inline style
  // before removing the class.
  const kbEl = document.querySelector(".skillmap-kb");
  const kbSvg = document.querySelector(".kb-brain-svg");
  if (kbEl && kbSvg) {
    kbEl.addEventListener("mouseenter", () => {
      kbEl.classList.add("is-spinning");
    });
    kbEl.addEventListener("mouseleave", () => {
      const matrix = getComputedStyle(kbSvg).transform;
      let angleDeg = 0;
      if (matrix && matrix !== "none") {
        const values = matrix.match(/matrix\(([^)]+)\)/);
        if (values) {
          const [a, b] = values[1].split(",").map(Number);
          angleDeg = Math.atan2(b, a) * (180 / Math.PI);
        }
      }
      kbEl.classList.remove("is-spinning");
      kbSvg.style.transform = `rotate(${angleDeg.toFixed(2)}deg)`;
    });
  }

  const SECTION_ORDER = ["capture", "sales", "people", "products", "qa", "technical"];
  const SECTION_LABEL = {
    capture: "Capture",
    sales: "Sales",
    people: "People",
    products: "Products",
    qa: "Knowledge Q&A",
    technical: "Technical",
  };

  const world = document.getElementById("skillmapWorld");
  const rotor = document.getElementById("skillmapRotor");
  const rotateControls = document.getElementById("skillmapRotateControls");
  const ghostName = document.getElementById("skillmapGhostName");
  const counts = document.getElementById("skillmapCounts");
  const defaultCountsText = counts.textContent;
  const backBtn = document.getElementById("skillmapBack");
  const edgeL = document.getElementById("skillmapEdgeL");
  const edgeR = document.getElementById("skillmapEdgeR");
  const edgeLLabel = document.getElementById("skillmapEdgeLLabel");
  const edgeRLabel = document.getElementById("skillmapEdgeRLabel");
  const chevL = document.getElementById("skillmapChevL");
  const chevR = document.getElementById("skillmapChevR");
  let rotorDeg = 0;

  // Sections View (operator, 2026-08-14: "No That didn't work, The Map
  // will be Hidden, and now this is a new view with a new layout we call
  // it Sections Views") — supersedes the earlier in-place dim/recenter
  // approach entirely. Every OTHER Section's tree/title/the KB/its
  // connector lines are hidden outright by the CSS's own
  // `.skillmap-world[data-focused] ...:not(.is-focused)` rules; this
  // function's job is just toggling the state classes/text those rules
  // and the edge-nav/back-button/ghost-name/counts-badge key off of.
  // The hover dim/highlight classes below are driven by real `mouseover`/
  // `mouseout` DOM events (see the delegated listeners further down) keyed
  // on `relatedTarget` containment — that check assumes the pointer moves
  // continuously between two STILL-VISIBLE elements. Focusing/unfocusing a
  // Section instead abruptly hides/shows/repositions elements out from
  // under a real cursor that never actually left, so no `mouseout` ever
  // fires and `.dimmed`/`.is-hovered` can get stuck (found live, 2026-08-14:
  // hover a Section, focus it, then go back — the hover glow stayed stuck
  // on it and every sibling stayed dimmed). Both `focusSection` and
  // `unfocus` clear this state outright before doing anything else, since
  // neither mode is a valid time for a leftover hover effect anyway.
  function clearHoverState() {
    document.querySelectorAll(".skillmap-tree, .skillmap-title").forEach((el) => {
      el.classList.remove("dimmed", "is-hovered");
    });
  }

  function focusSection(id) {
    clearHoverState();
    world.setAttribute("data-focused", id);
    document.querySelectorAll(".skillmap-tree").forEach((tree) => {
      tree.classList.toggle("is-focused", tree.dataset.sectionId === id);
    });
    document.querySelectorAll(".skillmap-title").forEach((title) => {
      title.classList.toggle("is-focused-title", title.dataset.sectionId === id);
    });
    // The "Section Rotation" wheel is a Default-map-only concept — reset
    // to 0deg so the focused tree's own hand-computed local offsets land
    // where they expect (this also resolves the previously-flagged open
    // gap: rotating the wheel then focusing a Section were never verified
    // together; forcing 0deg here sidesteps composing the two at all).
    rotor.style.setProperty("--wrot", "0deg");
    rotateControls.hidden = true;
    ghostName.textContent = SECTION_LABEL[id];
    const agentCount = document.querySelectorAll(
      `.skillmap-tree[data-section-id="${id}"] .skillmap-node`
    ).length;
    counts.textContent = `${SECTION_LABEL[id]} · ${agentCount} agent${agentCount === 1 ? "" : "s"}`;
    backBtn.hidden = false;
    const idx = SECTION_ORDER.indexOf(id);
    const prevId = SECTION_ORDER[(idx - 1 + SECTION_ORDER.length) % SECTION_ORDER.length];
    const nextId = SECTION_ORDER[(idx + 1) % SECTION_ORDER.length];
    edgeLLabel.textContent = SECTION_LABEL[prevId];
    edgeRLabel.textContent = SECTION_LABEL[nextId];
    edgeL.hidden = false;
    edgeR.hidden = false;
  }

  function unfocus() {
    clearHoverState();
    world.removeAttribute("data-focused");
    document.querySelectorAll(".skillmap-tree").forEach((tree) => tree.classList.remove("is-focused"));
    document.querySelectorAll(".skillmap-title").forEach((title) => title.classList.remove("is-focused-title"));
    rotor.style.setProperty("--wrot", rotorDeg + "deg");
    rotateControls.hidden = false;
    ghostName.textContent = "";
    counts.textContent = defaultCountsText;
    backBtn.hidden = true;
    edgeL.hidden = true;
    edgeR.hidden = true;
  }

  // Reference (checked live): the real click/hover target for entering a
  // Section is a large circular `.hit` region spanning the WHOLE section's
  // agent-scatter area (500x470px, real computed size), not just the small
  // icon button — operator, 2026-08-14: "Section is the Full Area not the
  // Hub Check the website". `[data-focus-target]` now matches both the hub
  // icon itself AND the new `.skillmap-tree-hit` region below it.
  document.querySelectorAll("[data-focus-target]").forEach((el) => {
    el.addEventListener("click", () => focusSection(el.dataset.focusTarget));
  });

  // Hover dim/highlight (operator, 2026-08-14: "when I hover a Section
  // Other Sections go Dimmed the title of that Section goes to a Yellow
  // Color and Zoomed in to 1.04x" — refined: "If we Hover on the Hub then
  // the Section a and the hub do the Hover Effect, if the Hover is on any
  // where empty on the section the Section do the hover Effect not the
  // items inside"). Delegated via bubbling `mouseover`/`mouseout` on each
  // `.skillmap-tree` itself (NOT the non-bubbling `mouseenter`/
  // `mouseleave`, and NOT a listener on just `.skillmap-tree-hit` alone) —
  // this is what makes hovering the hub, an empty hit-area point, or an
  // agent node all correctly trigger the SAME Section-level effect (any of
  // them is a descendant of the same `.skillmap-tree`, so the bubbled
  // event reaches this one listener either way), while moving BETWEEN
  // those children (e.g. hit-area -> hub) does not flicker on/off, since
  // `relatedTarget` is checked against the tree's own subtree each time.
  document.querySelectorAll(".skillmap-tree").forEach((tree) => {
    const sectionId = tree.dataset.sectionId;
    tree.addEventListener("mouseover", (e) => {
      if (tree.contains(e.relatedTarget)) return;
      document.querySelectorAll(".skillmap-tree, .skillmap-title").forEach((el) => {
        if (el.dataset.sectionId === sectionId) {
          if (el.classList.contains("skillmap-title")) el.classList.add("is-hovered");
        } else {
          el.classList.add("dimmed");
        }
      });
    });
    tree.addEventListener("mouseout", (e) => {
      if (tree.contains(e.relatedTarget)) return;
      document.querySelectorAll(".skillmap-tree, .skillmap-title").forEach((el) => {
        el.classList.remove("dimmed", "is-hovered");
      });
    });
  });

  backBtn.addEventListener("click", unfocus);

  chevL.addEventListener("click", () => {
    const current = world.getAttribute("data-focused");
    const idx = SECTION_ORDER.indexOf(current);
    focusSection(SECTION_ORDER[(idx - 1 + SECTION_ORDER.length) % SECTION_ORDER.length]);
  });

  chevR.addEventListener("click", () => {
    const current = world.getAttribute("data-focused");
    const idx = SECTION_ORDER.indexOf(current);
    focusSection(SECTION_ORDER[(idx + 1) % SECTION_ORDER.length]);
  });

  // --- Intro splash -------------------------------------------------------
  const intro = document.getElementById("skillmapIntro");
  document.getElementById("skillmapIntroEnter").addEventListener("click", () => {
    intro.hidden = true;
  });

  // --- Doctrine / outro panel ----------------------------------------------
  const about = document.getElementById("skillmapAbout");
  document.getElementById("skillmapAboutOpen").addEventListener("click", () => {
    about.hidden = false;
  });
  document.getElementById("skillmapAboutClose").addEventListener("click", () => {
    about.hidden = true;
  });
  about.querySelector(".skillmap-about-scrim").addEventListener("click", () => {
    about.hidden = true;
  });

  // --- Search palette -------------------------------------------------------
  const search = document.getElementById("skillmapSearch");
  const searchInput = document.getElementById("skillmapSearchInput");
  const searchResults = document.getElementById("skillmapSearchResults");
  const searchEmpty = document.getElementById("skillmapSearchEmpty");
  const searchResultEls = Array.from(searchResults.querySelectorAll(".skillmap-search-result"));

  function openSearch() {
    search.hidden = false;
    searchInput.value = "";
    filterSearch("");
    searchInput.focus();
  }

  function closeSearch() {
    search.hidden = true;
  }

  function filterSearch(query) {
    const q = query.trim().toLowerCase();
    let visibleCount = 0;
    searchResultEls.forEach((el) => {
      const match = !q || el.dataset.search.includes(q);
      el.hidden = !match;
      if (match) visibleCount += 1;
    });
    searchEmpty.hidden = visibleCount !== 0;
  }

  document.getElementById("skillmapSearchOpen").addEventListener("click", openSearch);
  search.querySelector(".skillmap-search-scrim").addEventListener("click", closeSearch);
  searchInput.addEventListener("input", (e) => filterSearch(e.target.value));
  searchResultEls.forEach((el) => {
    el.addEventListener("click", () => {
      closeSearch();
      openCard(el.dataset.agentId);
    });
  });

  document.addEventListener("keydown", (e) => {
    const isCmdK = (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k";
    if (isCmdK) {
      e.preventDefault();
      if (search.hidden) openSearch();
      else closeSearch();
      return;
    }
    if (e.key === "Escape") {
      if (!search.hidden) closeSearch();
      else if (!about.hidden) about.hidden = true;
      else if (cardOverlay.classList.contains("open")) closeCard();
    }
  });

  // --- Detail card ------------------------------------------------------
  const card = document.getElementById("skillmapCard");
  const cardOverlay = document.getElementById("skillmapCardOverlay");
  const cardTitle = document.getElementById("skillmapCardTitle");
  const cardClose = document.getElementById("skillmapCardClose");
  const agentPanels = Array.from(document.querySelectorAll(".skillmap-card-agent"));
  const AGENT_NAME = {
    "email-capture": "Email Capture",
    "meeting-capture": "Meeting Capture",
    "todo-capture": "To-Do Capture",
    "deal-capture": "Deal Capture",
    "pipeline-expert": "Pipeline Expert",
    "proposal-drafts": "Proposal Drafts",
    "people-notes": "People Notes",
    "feedback-capture": "Feedback Capture",
    "roadmap-expert": "Roadmap Expert",
    "changelog-drafts": "Changelog Drafts",
    "vault-qa": "Vault Q&A",
    "incident-capture": "Incident Capture",
    "systems-expert": "Systems Expert",
    "runbook-drafts": "Runbook Drafts",
  };

  function openCard(agentId) {
    agentPanels.forEach((el) => {
      el.hidden = el.dataset.agentDetail !== agentId;
    });
    cardTitle.textContent = AGENT_NAME[agentId] || agentId;
    card.classList.add("open");
    cardOverlay.classList.add("open");
  }

  function closeCard() {
    card.classList.remove("open");
    cardOverlay.classList.remove("open");
  }

  document.querySelectorAll(".skillmap-node[data-agent-id]").forEach((node) => {
    node.addEventListener("click", () => openCard(node.dataset.agentId));
  });
  cardClose.addEventListener("click", closeCard);
  cardOverlay.addEventListener("click", closeCard);

  // --- Fullscreen toggle (real behavior, harmless) ------------------------
  document.getElementById("skillmapFullscreen").addEventListener("click", () => {
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      document.documentElement.requestFullscreen().catch(() => {});
    }
  });

  // Section rotation (operator, 2026-08-14: "Section Rotation... Arrows at
  // the bottom so I can Rotate which section is at the top") — turns
  // `#skillmapRotor` 60deg per click (`rotor`/`rotorDeg` declared up with
  // `focusSection`/`unfocus`, which also read/reset them for the Sections
  // View). Accumulates rather than wrapping mod 360 so the CSS transition
  // always animates the SHORT way in the direction actually clicked,
  // instead of potentially snapping backwards on wraparound.
  document.getElementById("skillmapRotateLeft").addEventListener("click", () => {
    rotorDeg -= 60;
    rotor.style.setProperty("--wrot", rotorDeg + "deg");
  });
  document.getElementById("skillmapRotateRight").addEventListener("click", () => {
    rotorDeg += 60;
    rotor.style.setProperty("--wrot", rotorDeg + "deg");
  });
})();
