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
