// Screen state that survives a refresh (ADR-041, v10). The framework's own
// screens use the same two hooks, so a plugin and a framework page remember a
// selection the same way rather than each inventing it.
//
//   useUrlState         WHAT you are looking at -- the selected row, the
//                       filter, the active tab. Lives in the query string, so
//                       a refresh keeps it, Back undoes it, and the link can
//                       be sent to someone else.
//   useRememberedState  HOW you like to look at it -- a toggle, a default tab.
//                       Lives in localStorage, so it is still set tomorrow and
//                       does not clutter a shared link.
//
// Pick by that question, not by which is easier: a selection in localStorage
// makes two tabs fight over one value and makes a link mean something
// different for each person who opens it.

// `useUrlSelection` is the commonest shape of all -- an id that is selected or
// nothing -- and `useUrlFilters` is a whole filter bar, for the screen that
// would otherwise need a hook per field.
export { useUrlState, useUrlSelection, useUrlFilters, useRememberedState } from '../components/screenState';
