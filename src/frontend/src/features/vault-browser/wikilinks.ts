// `[[wikilink]]` / `[[target|alias]]` is Obsidian syntax, not CommonMark, so
// react-markdown renders it literally -- which is what the Cockpit summary showed
// (operator, 2026-09-24: "the Tagging SHould be COnverted to the Link now it shows
// [[ ]]"). Pre-processing it into ordinary markdown link syntax is the vault
// browser's own established approach (NoteBody.tsx); it lives here so the Cockpit
// uses the same rule rather than a second, subtly different one.

export const WIKILINK_PATTERN = /\[\[([^\]]+)\]\]/g;

/** Rewrites every `[[target]]` into a markdown link to that note, when the target
 * resolves to a real note. A target nothing resolves renders as its plain alias:
 * a link to a note that does not exist would be a promise the vault cannot keep,
 * and the brackets are noise either way. */
export function wikilinksToMarkdown(text: string, stems: Iterable<string>): string {
  const stemByLowerStem = new Map([...stems].map((stem) => [stem.toLowerCase(), stem]));
  return text.replace(WIKILINK_PATTERN, (_match, inner: string) => {
    const [rawTarget, rawAlias] = inner.split('|');
    const target = rawTarget.trim();
    const alias = (rawAlias ?? rawTarget).trim();
    const resolvedStem = stemByLowerStem.get(target.toLowerCase());
    if (!resolvedStem) return alias;
    return `[${alias}](/browse/${encodeURIComponent(resolvedStem)})`;
  });
}
