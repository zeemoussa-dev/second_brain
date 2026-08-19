import { useEffect, useMemo, useRef, useState } from 'react';
import type { AgentSection, MockAgent } from './mockAgents';

interface AgentsMapSearchPaletteProps {
  // fullAgents (AgentsMapPage.tsx) — the unreduced set, so a clustered/
  // overflowed agent is still findable by search even though it has no
  // dot of its own on the overview.
  agents: MockAgent[];
  sections: AgentSection[];
  onSelectAgent: (agentId: string) => void;
}

function capitalize(value: string): string {
  return value.length === 0 ? value : value[0].toUpperCase() + value.slice(1);
}

// Ctrl/Cmd+K command palette — ported from html-prototype/
// agents-map-skilltree-exploration.js's own openSearch/filterSearch
// (lines ~260-312). The prototype filters over each result's own
// hand-authored `data-search` keyword blob; MockAgent/AgentSummary carry
// no keywords field (only per-agent AgentDetail does, one fetch each — not
// worth paying for just to build a search index), so this indexes
// name/section/type instead — the real fields already available on this
// page (AgentsMapPage.tsx's own fullAgents/sections).
export function AgentsMapSearchPalette({ agents, sections, onSelectAgent }: AgentsMapSearchPaletteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement | null>(null);

  const sectionLabelById = useMemo(() => {
    const map = new Map<string, string>();
    sections.forEach((section) => map.set(section.id, section.label));
    return map;
  }, [sections]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const isCmdK = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k';
      if (isCmdK) {
        event.preventDefault();
        setIsOpen((open) => !open);
        return;
      }
      if (event.key === 'Escape') {
        setIsOpen((open) => (open ? false : open));
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    setQuery('');
    inputRef.current?.focus();
  }, [isOpen]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return agents;
    return agents.filter((agent) => {
      const haystack = `${agent.label} ${agent.type} ${sectionLabelById.get(agent.sectionId) ?? ''}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [agents, query, sectionLabelById]);

  function handleSelect(agentId: string) {
    setIsOpen(false);
    onSelectAgent(agentId);
  }

  return (
    <>
      <button
        type="button"
        className="map-search-trigger"
        onClick={() => setIsOpen(true)}
        aria-label="Search agents"
      >
        <span aria-hidden="true">&#8981;</span>
        <span>Search agents</span>
        <span className="map-search-kbd">Ctrl K</span>
      </button>
      {isOpen && (
        <div className="wizard-modal-overlay" onClick={() => setIsOpen(false)}>
          <div
            className="map-search-panel"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Search agents"
          >
            <input
              ref={inputRef}
              type="text"
              className="map-search-input"
              placeholder={`Search ${agents.length} agent${agents.length === 1 ? '' : 's'}…`}
              autoComplete="off"
              spellCheck={false}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <div className="map-search-results">
              {results.map((agent) => (
                <button
                  key={agent.id}
                  type="button"
                  className="map-search-result"
                  onClick={() => handleSelect(agent.id)}
                >
                  <span className="map-search-result-name">{agent.label}</span>
                  <span className="map-search-result-meta">
                    {sectionLabelById.get(agent.sectionId) ?? agent.sectionId} &middot; {capitalize(agent.type)}
                  </span>
                </button>
              ))}
            </div>
            {results.length === 0 && <p className="map-search-empty">No agents match.</p>}
          </div>
        </div>
      )}
    </>
  );
}
