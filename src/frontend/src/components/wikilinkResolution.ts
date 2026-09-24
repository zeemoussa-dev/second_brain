import { useEffect, useState } from 'react';
import { apiFetch } from '../api/client';
import { WIKILINK_PATTERN } from '../features/vault-browser/wikilinks';

// A `[[wikilink]]` used to become a link only where a surface remembered to work
// out which targets were real notes, and each one worked it out differently -- the
// note body from its own forwardLinks, the Cockpit from summary_links, a plugin
// from a field it added to its own API for the purpose. Chat, where agents write
// wikilinks constantly, resolved nothing and showed the brackets (`BUG-079`).
//
// So the answer is asked for centrally instead. Shipping the index to the browser
// is the wrong shape -- an install can index tens of thousands of notes, while a
// text mentions a dozen -- so a text asks about the targets it actually contains,
// and the answers are kept for the session: a stem's existence does not change
// between two renders of the same chat, and the same handful of notes
// (`[[ADNOC]]`) recur across every message.

const resolvedStemByTarget = new Map<string, string | null>();

// A chat mounts every message at once, and each one asks about its own targets. The
// asks are collected and sent as one request: the components of a single render all
// run their effects in the same task, so a microtask fires after the last of them.
// (Two batches can still overlap across ticks and ask about the same target twice --
// it is a cheap lookup, and the answer is cached the moment either lands.)
let pendingTargetByKey: Map<string, string> | null = null;
let pendingBatch: Promise<void> | null = null;

function targetKey(target: string): string {
  return target.trim().toLowerCase();
}

function askAbout(targets: string[]): Promise<void> {
  if (pendingTargetByKey === null) {
    pendingTargetByKey = new Map();
    pendingBatch = new Promise<void>((resolve, reject) => {
      queueMicrotask(() => {
        const batch = [...pendingTargetByKey!.values()];
        pendingTargetByKey = null;
        apiFetch<{ resolved: Record<string, string> }>('/vault-search/resolve', {
          method: 'POST',
          body: JSON.stringify({ targets: batch }),
        })
          .then(({ resolved }) => {
            for (const target of batch) {
              resolvedStemByTarget.set(targetKey(target), resolved[target] ?? null);
            }
            resolve();
          })
          .catch(reject);
      });
    });
  }
  for (const target of targets) pendingTargetByKey.set(targetKey(target), target);
  return pendingBatch!;
}

/** Every distinct `[[target]]` in the text, aliases stripped. */
export function wikilinkTargetsIn(text: string): string[] {
  const targets = new Set<string>();
  for (const [, inner] of text.matchAll(WIKILINK_PATTERN)) {
    const target = inner.split('|')[0].trim();
    if (target) targets.add(target);
  }
  return [...targets];
}

/** The real stems among these targets. Only the ones this session has not asked
 * about before reach the backend; a target that is not a note is remembered as
 * such, so an agent's favourite non-note never causes a second request. */
export async function resolveWikilinkTargets(targets: string[]): Promise<string[]> {
  const unknown = targets.filter((target) => !resolvedStemByTarget.has(targetKey(target)));
  if (unknown.length > 0) await askAbout(unknown);
  return targets
    .map((target) => resolvedStemByTarget.get(targetKey(target)))
    .filter((stem): stem is string => Boolean(stem));
}

/** The real stems among the text's wikilink targets, for passing to
 * `wikilinksToMarkdown`. Empty until the answer arrives, which renders those
 * targets as their plain alias -- the same thing an unresolvable target renders
 * as, and what every surface showed before this existed. */
export function useResolvedWikilinks(text: string, provided?: string[]): string[] {
  const [stems, setStems] = useState<string[]>(provided ?? []);

  useEffect(() => {
    if (provided) {
      setStems(provided);
      return;
    }
    const targets = wikilinkTargetsIn(text);
    if (targets.length === 0) {
      setStems([]);
      return;
    }
    let current = true;
    resolveWikilinkTargets(targets)
      .then((resolved) => {
        if (current) setStems(resolved);
      })
      .catch(() => {
        // An unreachable backend must not blank the text: the targets stay
        // unresolved and render as their aliases, exactly as an unknown note does.
        if (current) setStems([]);
      });
    return () => {
      current = false;
    };
    // `provided` is an array literal at most call sites, so depending on it by
    // identity would re-run this on every render; its contents are what matter.
  }, [text, provided?.join('\u0000')]);

  return stems;
}
