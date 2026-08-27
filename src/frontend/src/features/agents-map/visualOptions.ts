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
  // 2026-08-22 (operator: "very small amount") -- roughly doubled, biased
  // toward this app's own real domain (agents, pipelines, vault/data)
  // rather than generic filler.
  { id: 'hub', icon: 'hub', label: 'Hub' },
  { id: 'pipeline', icon: 'conveyor_belt', label: 'Pipeline' },
  { id: 'workflow', icon: 'account_tree', label: 'Workflow' },
  { id: 'route', icon: 'route', label: 'Route' },
  { id: 'bolt', icon: 'bolt', label: 'Bolt' },
  { id: 'database', icon: 'database', label: 'Database' },
  { id: 'inbox', icon: 'inbox', label: 'Inbox' },
  { id: 'send', icon: 'send', label: 'Send' },
  { id: 'description', icon: 'description', label: 'Description' },
  { id: 'auto', icon: 'auto_awesome', label: 'Auto' },
  { id: 'group', icon: 'group', label: 'Group' },
  { id: 'public', icon: 'public', label: 'Public' },
  { id: 'lock', icon: 'lock', label: 'Lock' },
  { id: 'verified', icon: 'verified', label: 'Verified' },
  // 2026-08-25 (operator: "more Icons Added to the Icon Set") -- second
  // expansion, biased toward this app's own newer real domains (customer
  // specialists, pricing, research, meetings) rather than generic filler,
  // same reasoning as the 2026-08-22 batch above.
  { id: 'handshake', icon: 'handshake', label: 'Handshake' },
  { id: 'apartment', icon: 'apartment', label: 'Company' },
  { id: 'cloud', icon: 'cloud', label: 'Cloud' },
  { id: 'architecture', icon: 'architecture', label: 'Architecture' },
  { id: 'payments', icon: 'payments', label: 'Payments' },
  { id: 'receipt', icon: 'receipt_long', label: 'Receipt' },
  { id: 'science', icon: 'science', label: 'Research' },
  { id: 'travel', icon: 'travel_explore', label: 'Discover' },
  { id: 'insights', icon: 'insights', label: 'Insights' },
  { id: 'schema', icon: 'schema', label: 'Schema' },
  { id: 'storage', icon: 'dns', label: 'Storage' },
  { id: 'network', icon: 'lan', label: 'Network' },
  { id: 'meeting', icon: 'groups', label: 'Meeting' },
  { id: 'person', icon: 'person', label: 'Person' },
  { id: 'library', icon: 'local_library', label: 'Library' },
  { id: 'shield', icon: 'shield', label: 'Shield' },
  { id: 'globe', icon: 'globe', label: 'Globe' },
  { id: 'sparkle', icon: 'auto_fix_high', label: 'Sparkle' },
  { id: 'flag', icon: 'flag', label: 'Flag' },
  { id: 'book', icon: 'menu_book', label: 'Book' },
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
  // 2026-08-25 (operator: "more Colors Including white") -- getIconColor
  // ForBackground's own luminance formula already handles a light swatch
  // correctly (>0.55 picks the dark on-accent icon color), so white needs
  // no special-casing there, just adding to the palette itself.
  '#ffffff',
  '#e9e4d6', // --color-text -- an off-white, softer than pure white against this app's own dark surfaces
  '#f59e0b',
  '#0d9488',
  '#8b5cf6',
  '#ea580c',
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

// 2026-08-22 (operator: "the Icon Colors should be Smart to go between
// dark and light based on the color") -- .agent-node--autonomous's own
// filled-node icon color was a single hardcoded token (--color-on-accent,
// dark) tuned for the 3 original Type colors only. Once a custom color
// from VISUAL_COLORS' full 10-swatch palette can be picked per agent
// (some genuinely dark, e.g. #4f46e5/#7c3aed/#b91c1c), a fixed dark icon
// goes invisible against them. Standard relative-luminance formula (WCAG's
// own simplified perceptual weighting -- green reads brighter to the eye
// than red or blue at the same numeric value) decides light-icon-on-dark
// vs dark-icon-on-light; the two return values are this app's own real
// --color-on-accent (dark) and --color-text (near-white) tokens, not new
// invented colors, so the result stays visually consistent with
// everywhere else those tokens are already used.
export function getIconColorForBackground(hex: string | null): string | undefined {
  if (!hex) return undefined;
  const match = /^#([0-9a-f]{6})$/i.exec(hex);
  if (!match) return undefined;
  const value = match[1];
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.55 ? 'var(--color-on-accent)' : 'var(--color-text)';
}
