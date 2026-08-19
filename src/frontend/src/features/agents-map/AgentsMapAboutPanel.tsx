import { useEffect, useState } from 'react';

interface AgentsMapAboutPanelProps {
  sectionCount: number;
  agentCount: number;
}

// Doctrine / "how to read this map" overlay — ported from html-prototype/
// agents-map-skilltree-exploration.html's own #skillmapAbout panel (lines
// ~213-231), rewritten against this app's real Section/Hub/ring model
// (concentric Worker/Expert/Producer rings via polarLayout.ts, not the
// prototype's own hex/tree layout — see AgentsMapCanvas.tsx). Reuses
// CreateAgentWizardModal.tsx's own .wizard-modal-* chrome classes rather
// than duplicating a second centered-overlay/panel treatment.
export function AgentsMapAboutPanel({ sectionCount, agentCount }: AgentsMapAboutPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsOpen(false);
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <>
      <button
        type="button"
        className="map-about-trigger"
        onClick={() => setIsOpen(true)}
        title="How to read this map"
        aria-label="How to read this map"
      >
        ?
      </button>
      {isOpen && (
        <div className="wizard-modal-overlay" onClick={() => setIsOpen(false)}>
          <div
            className="wizard-modal map-about-panel"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="How to read this map"
          >
            <div className="wizard-modal-header">
              <h2>How to read this map</h2>
              <button
                type="button"
                className="wizard-modal-close"
                onClick={() => setIsOpen(false)}
                aria-label="Close"
              >
                &times;
              </button>
            </div>
            <div className="wizard-modal-body">
              <p className="map-about-tag">
                {sectionCount} section{sectionCount === 1 ? '' : 's'} &middot; {agentCount} agent{agentCount === 1 ? '' : 's'} mapped &middot; 1 Knowledge Base
              </p>

              <div className="map-about-sec">THE RULE</div>
              <p>
                Every agent belongs to exactly one Section (a domain) and exactly one Type, which sets
                its ring: <b>Worker</b> (outermost — runs a recurring capture job), <b>Expert</b> (middle
                — answers questions over the vault), or <b>Producer</b> (innermost — maintains a living
                document). The Knowledge Base sits at the center; agents read from it and Producers
                write back to it.
              </p>

              <div className="map-about-sec">HUBS</div>
              <p>
                Each Section has one Hub. Click a Hub — or the space around it — to focus that Section
                full-size; the arrows at the edges of a focused Section page directly to the next Section
                without returning to the overview first.
              </p>

              <div className="map-about-sec">READING A NODE</div>
              <p>
                Click any agent to open its detail panel — settings, capabilities, and its assigned
                Skills. A dashed marker means more agents than fit on screen at once; click it to see the
                rest.
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
