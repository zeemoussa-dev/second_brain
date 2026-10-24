/** A search snippet with the query's own words marked.
 *
 * The highlight happens here and not in the API: the backend sends plain text,
 * so nothing has to escape a note's content on the way out or trust markup on
 * the way in. React escapes every piece below, so a note containing
 * `<script>` is shown, not run.
 */
export function SnippetText({ text, query }: { text: string; query: string }) {
  if (!text) return null;

  const terms = query
    .toLowerCase()
    .split(/[^a-z0-9]+/i)
    .filter((term) => term.length > 1);
  if (terms.length === 0) return <>{text}</>;

  // One pass, splitting on any term at once: highlighting term by term would
  // re-scan text it had already marked and nest the marks.
  const pattern = new RegExp(`(${terms.map(escapeForRegex).join('|')})`, 'gi');
  const pieces = text.split(pattern);

  return (
    <>
      {pieces.map((piece, index) =>
        // split() with one capture group alternates: text, match, text, …
        index % 2 === 1 ? (
          <mark className="snippet-match" key={index}>
            {piece}
          </mark>
        ) : (
          piece
        ),
      )}
    </>
  );
}

/** A query is whatever someone typed, so it can carry regex metacharacters —
 *  `c++` or `(draft)` would otherwise throw and take the result list with it. */
function escapeForRegex(term: string): string {
  return term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
