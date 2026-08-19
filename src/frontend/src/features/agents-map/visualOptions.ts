// Shared Visual-tab catalog (icon + color), reused by both the Agent
// detail panel and (once it gets its own settings surface) Section Hubs
// — one picker, one data shape, applied everywhere, per the operator's
// own framing ("all of the Hubs and Agents will have this"). Icons are
// rendered via the self-hosted Material Symbols icon font (tokens.css's
// own `.material-symbols-outlined` class + @font-face — operator,
// 2026-08-15: "Using Google Fonts there is one that is Icons Based...
// This will Beautify the UI Alot") — `icon` below is the font's own
// ligature name (e.g. "psychology"), not a raw glyph/emoji character;
// the font substitutes it with the real icon glyph via the `liga`
// OpenType feature. Replaces this catalog's earlier plain-emoji version.
export interface VisualIconOption {
  id: string;
  icon: string;
  label: string;
}

export const VISUAL_ICONS: VisualIconOption[] = [
  { id: 'brain', icon: 'psychology', label: 'Brain' },
  { id: 'mail', icon: 'mail', label: 'Mail' },
  { id: 'chat', icon: 'chat', label: 'Chat' },
  { id: 'chart', icon: 'bar_chart', label: 'Chart' },
  { id: 'tools', icon: 'build', label: 'Tools' },
  { id: 'gear', icon: 'settings', label: 'Gear' },
  { id: 'target', icon: 'track_changes', label: 'Target' },
  { id: 'files', icon: 'folder', label: 'Files' },
  { id: 'compass', icon: 'explore', label: 'Compass' },
  { id: 'star', icon: 'star', label: 'Star' },
  { id: 'search', icon: 'search', label: 'Search' },
  { id: 'calendar', icon: 'calendar_month', label: 'Calendar' },
  { id: 'bell', icon: 'notifications', label: 'Bell' },
  { id: 'link', icon: 'link', label: 'Link' },
];

// Curated palette: this app's own real accent + Agent-type tokens
// (tokens.css) first, then a handful of extra distinguishable hues —
// never an open-ended color picker, so every choice stays legible
// against the dark theme.
// Comments below name the CSS token each value backs, where one exists —
// kept in sync with tokens.css's own --agent-color-* reassignment
// (operator, 2026-08-15: "Workers/Jobs to be White, Experts to have a
// Color That Matches our design, Producers a different color"): worker's
// own default is --color-text (not a fixed hex, so no entry here), expert
// reuses --color-accent, producer now points at #65a30d instead of the
// old #7c3aed. The old #2563eb/#7c3aed/#db2777 trio stays in the picker
// as plain unlabeled swatches — still valid manual per-agent/Section
// override choices, just no longer any Type's own automatic default.
export const VISUAL_COLORS: string[] = [
  '#c58b5f', // --color-accent / --agent-color-expert
  '#65a30d', // --agent-color-producer
  '#2563eb',
  '#7c3aed',
  '#db2777',
  '#16a34a', // --color-success
  '#b45309', // --color-warning
  '#b91c1c', // --color-danger
  '#0891b2',
  '#4f46e5',
];

// Operator, 2026-08-16: "icons still not visible on agents" — VISUAL_ICONS
// is a curated 14-entry whitelist keyed by picker `id` (e.g. 'brain' ->
// ligature 'psychology'), used when a real user picks one via
// VisualPicker.tsx (which calls onSelectIcon(icon.id)). But sample_data.py
// (and any other API-supplied agent.icon) sets RAW Material Symbols
// ligature names directly ('handshake', 'download', 'category', ...) —
// the SAME convention SectionHub.tsx already uses for section.icon with no
// lookup at all. Doing an `.id`-only lookup here silently dropped every
// icon that wasn't coincidentally both a valid id AND its own ligature
// (only 'mail'/'search' qualified). Falling back to the raw value lets
// both conventions render: a picker-set id still resolves through the
// curated list, anything else is assumed to already BE a ligature name.
export function getVisualIconName(iconId: string | null): string | null {
  if (!iconId) return null;
  return VISUAL_ICONS.find((icon) => icon.id === iconId)?.icon ?? iconId;
}
