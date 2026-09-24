import { useEffect, useRef, useState } from 'react';

// Renders a ```mermaid fenced block as a real diagram (operator, 2026-09-24: the
// CBO agent writes them constantly). A framework component, not a plugin: this is
// the markdown renderer learning one more block type, the same as an image or a
// code block, and it carries no knowledge of anyone's business. Every surface that
// renders markdown gets it at once -- chat, note bodies, Cockpit summaries.
//
// Two deliberate choices:
//
// - **Loaded on demand.** mermaid is large, and most pages never show a diagram,
//   so it is imported the first time one appears rather than bundled into the
//   initial load.
// - **`securityLevel: 'strict'`.** Mermaid renders to SVG, which has to be
//   inserted as markup -- the one place this app does that, against ChatMessageText's
//   own zero-raw-HTML rule (`ADR-050`). Strict is what makes it safe: mermaid
//   sanitizes the diagram's own labels and refuses click/script directives, so a
//   diagram written by an agent cannot smuggle HTML through the fence.
//
// A diagram that does not parse renders as the code the agent wrote, with the
// reason above it: an unreadable diagram is still information, and silently
// dropping it would hide that the agent wrote something malformed.

interface MermaidDiagramProps {
  code: string;
}

let mermaidReady: Promise<typeof import('mermaid').default> | null = null;

function loadMermaid() {
  if (!mermaidReady) {
    mermaidReady = import('mermaid').then(({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'strict',
        // The app is dark throughout (`tokens.css` sets `color-scheme: dark`), so
        // the diagram follows rather than punching a white box into the page.
        theme: 'dark',
        fontFamily: 'inherit',
      });
      return mermaid;
    });
  }
  return mermaidReady;
}

let diagramCount = 0;

export function MermaidDiagram({ code }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const idRef = useRef(`mermaid-${(diagramCount += 1)}`);

  useEffect(() => {
    let cancelled = false;
    setSvg(null);
    setProblem(null);
    loadMermaid()
      .then((mermaid) => mermaid.render(idRef.current, code))
      .then(({ svg: rendered }) => !cancelled && setSvg(rendered))
      .catch((error: unknown) => {
        if (!cancelled) {
          setProblem(error instanceof Error ? error.message : 'the diagram could not be drawn');
        }
      });
    return () => {
      cancelled = true;
    };
  }, [code]);

  if (problem !== null) {
    return (
      <div className="mermaid-diagram mermaid-diagram--failed">
        <p className="text-muted">This diagram could not be drawn: {problem}</p>
        <pre><code>{code}</code></pre>
      </div>
    );
  }
  if (svg === null) {
    return <p className="text-muted mermaid-diagram-loading" role="status">Drawing the diagram…</p>;
  }
  // Mermaid's own generated SVG, sanitized by `securityLevel: 'strict'` above.
  return <div className="mermaid-diagram" dangerouslySetInnerHTML={{ __html: svg }} />;
}
