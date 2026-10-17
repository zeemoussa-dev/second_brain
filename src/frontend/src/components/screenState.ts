// Screen state that survives a refresh (ADR-041). Four hooks, because there
// are two different things people call "remembering":
//
//   useUrlState         WHAT you are looking at -- the active tab, a sort
//   useUrlSelection     order, the selected row, a whole filter bar. Lives in
//   useUrlFilters       the query string, so a refresh keeps it, Back undoes
//                       it, and the link can be sent to someone else.
//   useRememberedState  HOW you like to look at it -- a toggle, a default tab.
//                       Lives in localStorage, so it is still set tomorrow and
//                       does not clutter a shared link.
//
// Pick by that question, not by which is easier: a selection in localStorage
// makes two tabs fight over one value and makes a link mean something
// different for each person who opens it.
//
// All four take an updater function as well as a value, because they are
// drop-in replacements for `useState` and a screen written against it already
// calls `setThing((previous) => ...)`.

import { useCallback, useEffect, useMemo, useRef, useState, type Dispatch, type SetStateAction } from 'react';
import { useSearchParams } from 'react-router';

function resolve<T>(next: SetStateAction<T>, previous: T): T {
  return typeof next === 'function' ? (next as (previous: T) => T)(previous) : next;
}

/** A value held in the query string, with the ergonomics of `useState`.
 *
 * A value equal to `fallback` is REMOVED from the URL rather than written, so
 * an untouched screen has a clean address and a shared link carries only what
 * was actually chosen.
 *
 * Writes replace the history entry instead of pushing one: a filter changed
 * five times should not cost five presses of Back to leave the page. Pass
 * `{ history: 'push' }` for a change that is a navigation in its own right --
 * opening a record the reader will expect Back to close.
 *
 * Pass `valid` for a value with a fixed set of options -- a tab, a sort order.
 * A URL is typed, bookmarked and edited by hand, so anything outside the set
 * reads as the fallback instead of putting the screen into a state it has no
 * rendering for. It also narrows the type, so a tab stays a tab. */
export function useUrlState<T extends string = string>(
  key: string,
  fallback: T = '' as T,
  options: { history?: 'replace' | 'push'; valid?: readonly T[] } = {},
): [T, Dispatch<SetStateAction<T>>] {
  const [searchParams, setSearchParams] = useSearchParams();
  const { history, valid } = options;

  const read = useCallback((params: URLSearchParams): T => {
    const raw = params.get(key);
    const known = raw !== null && (valid === undefined || valid.includes(raw as T));
    return known ? (raw as T) : fallback;
  }, [key, fallback, valid]);

  const value = read(searchParams);

  const setValue = useCallback<Dispatch<SetStateAction<T>>>((next) => {
    setSearchParams((current) => {
      // Build from `current` rather than from a captured copy: two values set
      // in one event (clearing a filter and its page number) must not drop
      // each other's write, and an updater must see what is in the URL now.
      const params = new URLSearchParams(current);
      const resolved = resolve(next, read(params));
      if (resolved === fallback || resolved === '') {
        params.delete(key);
      } else {
        params.set(key, resolved);
      }
      return params;
    }, { replace: history !== 'push' });
  }, [key, fallback, history, read, setSearchParams]);

  return [value, setValue];
}

/** The commonest selection shape: an id that is selected, or nothing.
 *
 * A thin wrapper over `useUrlState` that speaks `null` instead of `''`, so a
 * screen keeps the `string | null` surface its panels and props already expect
 * and does not hand-write the same conversion. Nothing selected means no
 * parameter in the URL at all. */
export function useUrlSelection(
  key: string,
  options: { history?: 'replace' | 'push' } = {},
): [string | null, Dispatch<SetStateAction<string | null>>] {
  const [value, setValue] = useUrlState<string>(key, '', options);
  const selection = value === '' ? null : value;

  const setSelection = useCallback<Dispatch<SetStateAction<string | null>>>((next) => {
    setValue((previous) => resolve(next, previous === '' ? null : previous) ?? '');
  }, [setValue]);

  return [selection, setSelection];
}

/** A whole filter bar held in the query string.
 *
 * The case `useUrlState` is clumsy for: a screen with a dozen optional filters
 * does not want a dozen hooks. `defaults` names every field and supplies the
 * value each one falls back to, so a field absent from the URL is absent from
 * the filters, and a field set back to its default is dropped from the URL.
 *
 * Booleans are inferred from the defaults rather than declared separately: a
 * field whose default is a boolean reads `true` as true and anything else as
 * false. Unknown parameters are ignored, so one screen's filters do not
 * swallow another's selection on a shared address. */
export function useUrlFilters<T extends Record<string, string | boolean | undefined>>(
  defaults: T,
): [T, (field: keyof T & string, value: string | boolean) => void] {
  const [searchParams, setSearchParams] = useSearchParams();

  // Memoised on the VALUES, not rebuilt per render. A filter object is what a
  // screen passes to `useEffect`, and a fresh identity every render turns that
  // effect into an infinite loop -- fetch, setState, re-render, fetch -- which
  // on the Action Center showed up as the board flashing (2026-10-17).
  const search = searchParams.toString();
  const defaultsKey = JSON.stringify(defaults);
  const filters = useMemo(() => {
    const resolved = { ...defaults };
    const params = new URLSearchParams(search);
    for (const field of Object.keys(defaults) as (keyof T & string)[]) {
      const raw = params.get(field);
      if (raw === null) continue;
      (resolved as Record<string, string | boolean | undefined>)[field] =
        typeof defaults[field] === 'boolean' ? raw === 'true' : raw;
    }
    return resolved;
    // `defaults` is a literal rebuilt every render, so its VALUES are depended
    // on through defaultsKey rather than its identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, defaultsKey]);

  // `defaults` is a literal rebuilt on every render, so it is compared by
  // value inside the setter rather than depended on by identity here.
  const latestDefaults = useRef(defaults);
  latestDefaults.current = defaults;

  const setField = useCallback((field: keyof T & string, value: string | boolean) => {
    setSearchParams((current) => {
      const params = new URLSearchParams(current);
      const fallback = latestDefaults.current[field];
      const isDefault = value === fallback
        || (fallback === undefined && (value === '' || value === false));
      if (isDefault) {
        params.delete(field);
      } else {
        params.set(field, String(value));
      }
      return params;
    }, { replace: true });
  }, [setSearchParams]);

  return [filters, setField];
}

const STORAGE_PREFIX = 'second-brain:';

function readStored<T>(key: string, fallback: T): T {
  // Storage can throw outright, not merely return null: Safari's private mode
  // and a browser set to block site data both raise on access. A preference is
  // never worth a blank screen, so every path falls back to the default.
  try {
    const raw = window.localStorage.getItem(STORAGE_PREFIX + key);
    return raw === null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

/** A preference remembered across visits, with the ergonomics of `useState`.
 *
 * For how a screen is set up, never for what is selected on it. The value is
 * JSON, so booleans, numbers and small objects all work.
 *
 * `key` is namespaced per plugin by convention -- `action-center.chase-inside`
 * -- because localStorage is one flat space shared by the whole app. */
export function useRememberedState<T>(key: string, fallback: T): [T, Dispatch<SetStateAction<T>>] {
  const [value, setValue] = useState<T>(() => readStored(key, fallback));

  // The first render already read storage; writing on that render would put
  // the default back for a key nobody has touched yet, and would overwrite a
  // value another tab wrote a moment ago.
  const isFirstRender = useRef(true);
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
    } catch {
      // Out of quota, or site data blocked. The screen still works for this
      // visit; only the remembering is lost.
    }
  }, [key, value]);

  return [value, setValue];
}
