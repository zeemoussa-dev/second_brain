import GithubSlugger from 'github-slugger';

// Shared by NoteBody.tsx (which assigns each rendered heading a real
// `id` via the `rehype-slug` plugin -- same underlying `github-slugger`
// library used here) and NoteDetailPage.tsx (renders the jump-to-section
// list against those same ids). Using the identical library both places
// is what keeps them from disagreeing about what a given anchor is
// called -- an earlier hand-rolled version of this file computed its
// own slugs independently of `rehype-slug`'s real ones and produced
// mismatched ids the moment React re-invoked a render (confirmed live,
// 2026-08-24: StrictMode double-invoking a render-time mutable counter
// desynced them after the very first heading). `GithubSlugger` is a
// pure function of the heading text alone (a fresh instance per call
// here, matching a fresh `rehype-slug` pass per render) -- no counter
// mutated during React's own render, so it can never desync.
export interface TocHeading {
  level: 2 | 3;
  text: string;
  slug: string;
}

const HEADING_LINE_PATTERN = /^(#{2,3})\s+(.+)$/gm;

// A real vault note can legitimately repeat the same heading text more
// than once (e.g. two "## Related" sections in different parts of a
// long capture) -- GithubSlugger's own built-in dedup (a numeric suffix
// on a repeat) handles this the exact same way `rehype-slug` does.
export function extractHeadings(body: string): TocHeading[] {
  const slugger = new GithubSlugger();
  const headings: TocHeading[] = [];
  for (const match of body.matchAll(HEADING_LINE_PATTERN)) {
    const level = match[1].length as 2 | 3;
    const text = match[2].trim();
    headings.push({ level, text, slug: slugger.slug(text) });
  }
  return headings;
}

export interface SectionRange {
  /** The rendered heading's id, or null for the text above the first
   *  heading — which is a real part of the note and must be editable too. */
  slug: string | null;
  text: string;
  /** Where this section starts in the raw body: the heading line itself, so
   *  editing a section lets you fix its title without leaving it. */
  start: number;
  /** The next heading's start, or the end of the note. */
  end: number;
}

/** The note split at its headings (operator, 2026-10-24: clicking the text
 *  "Turns into a Plain for the Whole Document and Its not anymore that Section
 *  I am Clicking").
 *
 * Editing a 4,000-word capture as one textarea loses the place you clicked and
 * puts every other section at risk of a stray keystroke. Splitting at heading
 * boundaries is safe because a heading always starts its own line, so each
 * slice is still whole markdown.
 */
export function sectionRanges(body: string): SectionRange[] {
  const slugger = new GithubSlugger();
  const matches = [...body.matchAll(HEADING_LINE_PATTERN)];
  const sections: SectionRange[] = [];

  const firstHeadingAt = matches.length ? matches[0].index ?? body.length : body.length;
  if (body.slice(0, firstHeadingAt).trim().length > 0) {
    sections.push({ slug: null, text: 'the opening', start: 0, end: firstHeadingAt });
  }

  matches.forEach((match, position) => {
    const start = match.index ?? 0;
    sections.push({
      slug: slugger.slug(match[2].trim()),
      text: match[2].trim(),
      start,
      end: position + 1 < matches.length ? matches[position + 1].index ?? body.length : body.length,
    });
  });
  return sections;
}

export interface EmptySection {
  slug: string;
  text: string;
  /** Where the caret goes when the operator clicks "add": the character after
   *  this heading's own line, which is where the missing content belongs. */
  offset: number;
}

/** The headings with nothing under them (operator, 2026-10-24: "When a Section
 *  is Empty like Summary for example (Show No Summary and I can Click to edit
 *  it)").
 *
 * A template puts the headings in and an agent fills them, so an empty one is
 * the normal state of a note nobody has got to yet -- and it renders as a
 * heading floating above the next heading, which reads like a glitch rather
 * than like work to do. Slugged with the SAME library as the headings
 * themselves, so a placeholder can be matched to its rendered heading by id.
 */
export function findEmptySections(body: string): EmptySection[] {
  const slugger = new GithubSlugger();
  const empty: EmptySection[] = [];
  const matches = [...body.matchAll(HEADING_LINE_PATTERN)];
  matches.forEach((match, position) => {
    const slug = slugger.slug(match[2].trim());
    const from = (match.index ?? 0) + match[0].length;
    const to = position + 1 < matches.length ? matches[position + 1].index ?? body.length : body.length;
    if (body.slice(from, to).trim().length === 0) {
      empty.push({ slug, text: match[2].trim(), offset: from });
    }
  });
  return empty;
}
