import { useEffect, useRef, useState, type CSSProperties } from 'react';

// Generic clamp-then-expand for a kv-row's own long free-text value
// (operator, 2026-08-30: "Purpose Description and any feild with long
// text (prompt) should be showing 3 lines only with a read more to
// click on to expand instead of covering half of the panel in text").
// A DIFFERENT call than the same day's earlier .item-row fix (Skills
// list, Pipeline Steps list) -- that one deliberately wraps in full,
// no cap, because a list row is already itemized/bounded by its own
// row; a kv-row's own Description/Purpose/Guardrails value has no such
// natural boundary and a long one really does push the rest of the
// panel's fields out of view, which is the exact complaint here.
// Detects whether clamping actually did anything (scrollHeight >
// clientHeight once painted) so short values never grow a pointless
// "Read more" button that would toggle nothing.
interface ExpandableTextProps {
  text: string;
  maxLines?: number;
}

export function ExpandableText({ text, maxLines = 3 }: ExpandableTextProps) {
  const [expanded, setExpanded] = useState(false);
  const [isClamped, setIsClamped] = useState(false);
  const textRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = textRef.current;
    if (!el) return;
    setIsClamped(el.scrollHeight > el.clientHeight + 1);
    // Re-measure only when the real text itself changes -- `expanded`
    // deliberately excluded: once a value is known to overflow 3 lines
    // it stays "clampable" regardless of which state it's currently
    // rendered in, so the toggle button never disappears mid-use.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  return (
    <span className="expandable-text-wrapper">
      <span
        ref={textRef}
        className={expanded ? 'expandable-text' : 'expandable-text expandable-text--clamped'}
        style={expanded ? undefined : ({ WebkitLineClamp: maxLines } as CSSProperties)}
      >
        {text}
      </span>
      {isClamped && (
        <button
          type="button"
          className="expandable-text-toggle"
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? 'Show less' : 'Read more'}
        </button>
      )}
    </span>
  );
}
