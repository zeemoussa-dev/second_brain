// The frontend half of the Plugin API (ADR-022): the only framework module a
// plugin's screens may import, apart from the contract in ./types. A screen
// that imports anything else from the framework -- a feature, a page, the
// API client directly -- breaks the next time that module changes, even
// though its framework_api still matches.

export { apiFetch, ApiError } from '../api/client';
