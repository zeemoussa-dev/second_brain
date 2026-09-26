// Obsidian callouts (`> [!info] Title`) as real markdown AST, not HTML.
//
// A callout is a blockquote whose first line carries a type marker. It is not
// CommonMark, so every surface printed the marker as text inside a quote --
// `[!abstract]`, `[!info]`, `[!success]` read as literal text on 367 of the
// reporting vault's notes (`BUG-080`).
//
// This is a remark transform rather than a rendered-HTML pass on purpose: the
// off-the-shelf plugin for this replaces the first paragraph with a raw `html`
// node, which react-markdown drops unless `rehype-raw` is on -- so the callout's
// own first line would vanish. The app renders no raw HTML anywhere (`ADR-050`),
// so the marker is turned into node data instead: the blockquote gets a class and
// a `data-callout` type, the first line becomes the title, and everything else
// stays the ordinary markdown it already was.

interface MarkdownNode {
  type: string;
  value?: string;
  children?: MarkdownNode[];
  data?: { hProperties?: Record<string, unknown> };
}

const CALLOUT_MARKER = /^\[!([A-Za-z][A-Za-z-]*)\]([+-]?)[ \t]*/;

/** The inline nodes of the first line, and everything after it. A soft line break
 * lives inside a text node's own value, so the split can fall mid-node. */
function splitAtFirstLine(children: MarkdownNode[]): [MarkdownNode[], MarkdownNode[]] {
  const firstLine: MarkdownNode[] = [];
  const rest: MarkdownNode[] = [];
  let past = false;
  for (const child of children) {
    if (past) {
      rest.push(child);
      continue;
    }
    const newlineAt = child.type === 'text' ? (child.value ?? '').indexOf('\n') : -1;
    if (newlineAt === -1) {
      // A hard break ends the line without carrying a newline of its own.
      if (child.type === 'break') past = true;
      else firstLine.push(child);
      continue;
    }
    const before = (child.value ?? '').slice(0, newlineAt);
    const after = (child.value ?? '').slice(newlineAt + 1);
    if (before) firstLine.push({ type: 'text', value: before });
    if (after) rest.push({ type: 'text', value: after });
    past = true;
  }
  return [firstLine, rest];
}

function isBlank(children: MarkdownNode[]): boolean {
  return children.every((child) => child.type === 'text' && !(child.value ?? '').trim());
}

function asCallout(quote: MarkdownNode): void {
  const [firstBlock, ...laterBlocks] = quote.children ?? [];
  if (!firstBlock || firstBlock.type !== 'paragraph') return;
  const [leading] = firstBlock.children ?? [];
  if (!leading || leading.type !== 'text') return;
  const marker = CALLOUT_MARKER.exec(leading.value ?? '');
  if (!marker) return;

  const type = marker[1].toLowerCase();
  const withoutMarker = [
    { type: 'text', value: (leading.value ?? '').slice(marker[0].length) },
    ...(firstBlock.children ?? []).slice(1),
  ];
  const [titleChildren, bodyChildren] = splitAtFirstLine(withoutMarker);

  const blocks: MarkdownNode[] = [];
  blocks.push({
    type: 'paragraph',
    // An untitled callout still gets its title row, carrying the type's own name
    // -- which is what Obsidian shows, and what the icon hangs off.
    children: isBlank(titleChildren) ? [] : titleChildren,
    data: { hProperties: { className: 'callout-title' } },
  });
  if (bodyChildren.length > 0 && !isBlank(bodyChildren)) {
    blocks.push({ type: 'paragraph', children: bodyChildren });
  }
  quote.children = [...blocks, ...laterBlocks];
  quote.data = {
    ...quote.data,
    hProperties: {
      ...(quote.data?.hProperties ?? {}),
      className: `callout callout-${type}`,
      'data-callout': type,
    },
  };
}

function walk(node: MarkdownNode): void {
  if (node.type === 'blockquote') asCallout(node);
  for (const child of node.children ?? []) walk(child);
}

export function remarkCallouts() {
  return (tree: MarkdownNode) => {
    walk(tree);
  };
}
