// The central Knowledge Base element — a dense neuron-mesh "brain" SVG
// ported verbatim from html-prototype/agents-map.html (23 neurons: 16 outer
// ring + 6 mid ring + 1 center, ~42 crossing synapse lines, 2 traveling
// pulse dots). Static approved-design SVG, not derived from polarLayout.

export function KnowledgeBaseNode() {
  return (
    <div className="kb-node">
      <svg className="kb-brain-svg" viewBox="0 0 100 100">
        <line x1="50" y1="10" x2="65.3" y2="13" />
        <line x1="65.3" y1="13" x2="78.3" y2="21.7" />
        <line x1="78.3" y1="21.7" x2="87" y2="34.7" />
        <line x1="87" y1="34.7" x2="90" y2="50" />
        <line x1="90" y1="50" x2="87" y2="65.3" />
        <line x1="87" y1="65.3" x2="78.3" y2="78.3" />
        <line x1="78.3" y1="78.3" x2="65.3" y2="87" />
        <line x1="65.3" y1="87" x2="50" y2="90" />
        <line x1="50" y1="90" x2="34.7" y2="87" />
        <line x1="34.7" y1="87" x2="21.7" y2="78.3" />
        <line x1="21.7" y1="78.3" x2="13" y2="65.3" />
        <line x1="13" y1="65.3" x2="10" y2="50" />
        <line x1="10" y1="50" x2="13" y2="34.7" />
        <line x1="13" y1="34.7" x2="21.7" y2="21.7" />
        <line x1="21.7" y1="21.7" x2="34.7" y2="13" />
        <line x1="34.7" y1="13" x2="50" y2="10" />
        <line x1="61" y1="30.95" x2="72" y2="50" />
        <line x1="72" y1="50" x2="61" y2="69.05" />
        <line x1="61" y1="69.05" x2="39" y2="69.05" />
        <line x1="39" y1="69.05" x2="28" y2="50" />
        <line x1="28" y1="50" x2="39" y2="30.95" />
        <line x1="39" y1="30.95" x2="61" y2="30.95" />
        <line x1="61" y1="30.95" x2="50" y2="50" />
        <line x1="72" y1="50" x2="50" y2="50" />
        <line x1="61" y1="69.05" x2="50" y2="50" />
        <line x1="39" y1="69.05" x2="50" y2="50" />
        <line x1="28" y1="50" x2="50" y2="50" />
        <line x1="39" y1="30.95" x2="50" y2="50" />
        <line x1="61" y1="30.95" x2="65.3" y2="13" />
        <line x1="61" y1="30.95" x2="78.3" y2="21.7" />
        <line x1="72" y1="50" x2="87" y2="34.7" />
        <line x1="72" y1="50" x2="87" y2="65.3" />
        <line x1="61" y1="69.05" x2="78.3" y2="78.3" />
        <line x1="61" y1="69.05" x2="65.3" y2="87" />
        <line x1="39" y1="69.05" x2="34.7" y2="87" />
        <line x1="39" y1="69.05" x2="21.7" y2="78.3" />
        <line x1="28" y1="50" x2="13" y2="65.3" />
        <line x1="28" y1="50" x2="13" y2="34.7" />
        <line x1="39" y1="30.95" x2="21.7" y2="21.7" />
        <line x1="39" y1="30.95" x2="34.7" y2="13" />
        <line x1="65.3" y1="13" x2="34.7" y2="87" />
        <line x1="87" y1="65.3" x2="13" y2="34.7" />
        <circle className="kb-neuron" cx="50" cy="10" r="3.4" fillOpacity="0.9" style={{ animationDelay: '0s' }} />
        <circle className="kb-neuron" cx="65.3" cy="13" r="2.8" fillOpacity="0.7" style={{ animationDelay: '0.1s' }} />
        <circle className="kb-neuron" cx="78.3" cy="21.7" r="3.1" fillOpacity="0.85" style={{ animationDelay: '0.2s' }} />
        <circle className="kb-neuron" cx="87" cy="34.7" r="2.6" fillOpacity="0.6" style={{ animationDelay: '0.3s' }} />
        <circle className="kb-neuron" cx="90" cy="50" r="3.4" fillOpacity="0.9" style={{ animationDelay: '0.4s' }} />
        <circle className="kb-neuron" cx="87" cy="65.3" r="2.8" fillOpacity="0.7" style={{ animationDelay: '0.5s' }} />
        <circle className="kb-neuron" cx="78.3" cy="78.3" r="3.1" fillOpacity="0.85" style={{ animationDelay: '0.6s' }} />
        <circle className="kb-neuron" cx="65.3" cy="87" r="2.6" fillOpacity="0.6" style={{ animationDelay: '0.7s' }} />
        <circle className="kb-neuron" cx="50" cy="90" r="3.4" fillOpacity="0.9" style={{ animationDelay: '0.8s' }} />
        <circle className="kb-neuron" cx="34.7" cy="87" r="2.8" fillOpacity="0.7" style={{ animationDelay: '0.9s' }} />
        <circle className="kb-neuron" cx="21.7" cy="78.3" r="3.1" fillOpacity="0.85" style={{ animationDelay: '1.0s' }} />
        <circle className="kb-neuron" cx="13" cy="65.3" r="2.6" fillOpacity="0.6" style={{ animationDelay: '1.1s' }} />
        <circle className="kb-neuron" cx="10" cy="50" r="3.4" fillOpacity="0.9" style={{ animationDelay: '1.2s' }} />
        <circle className="kb-neuron" cx="13" cy="34.7" r="2.8" fillOpacity="0.7" style={{ animationDelay: '1.3s' }} />
        <circle className="kb-neuron" cx="21.7" cy="21.7" r="3.1" fillOpacity="0.85" style={{ animationDelay: '1.4s' }} />
        <circle className="kb-neuron" cx="34.7" cy="13" r="2.6" fillOpacity="0.6" style={{ animationDelay: '1.5s' }} />
        <circle className="kb-neuron" cx="61" cy="30.95" r="2.4" fillOpacity="0.65" style={{ animationDelay: '1.6s' }} />
        <circle className="kb-neuron" cx="72" cy="50" r="2.2" fillOpacity="0.55" style={{ animationDelay: '1.75s' }} />
        <circle className="kb-neuron" cx="61" cy="69.05" r="2.4" fillOpacity="0.65" style={{ animationDelay: '1.9s' }} />
        <circle className="kb-neuron" cx="39" cy="69.05" r="2.2" fillOpacity="0.55" style={{ animationDelay: '2.05s' }} />
        <circle className="kb-neuron" cx="28" cy="50" r="2.4" fillOpacity="0.65" style={{ animationDelay: '2.2s' }} />
        <circle className="kb-neuron" cx="39" cy="30.95" r="2.2" fillOpacity="0.55" style={{ animationDelay: '2.35s' }} />
        <circle className="kb-neuron" cx="50" cy="50" r="5" fillOpacity="1" style={{ animationDelay: '0s' }} />
        <circle className="kb-pulse-dot" r="1.8">
          <animateMotion dur="2.4s" repeatCount="indefinite" path="M65.3,13 L34.7,87" />
        </circle>
        <circle className="kb-pulse-dot" r="1.8">
          <animateMotion dur="2.8s" begin="0.7s" repeatCount="indefinite" path="M87,65.3 L13,34.7" />
        </circle>
      </svg>
      <span className="kb-node-label">
        Knowledge Base
        <span className="kb-node-sub">Vault indexed</span>
      </span>
    </div>
  );
}
