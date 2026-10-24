/** Applying this install's theme to the live document (operator, 2026-10-24).
 *
 * Three things reach the page, and each is the cheapest mechanism that can
 * carry it: `data-theme` and `data-font` are attributes on <html>, because
 * both are one of a few known values and the stylesheet owns what they mean;
 * the accent is a custom property, because it is a free colour the stylesheet
 * cannot enumerate.
 *
 * **The text colour on the accent is computed, not stored.** An operator who
 * picks a pale accent gets dark text on their buttons and a dark accent gets
 * light text — the alternative is the white-on-white this app has now shipped
 * twice (the Agents Map's filled worker node, and the Marketplace's install
 * result), both times because a foreground was fixed while a background moved.
 */

export interface ThemeChoice {
  theme_mode: string;
  font: string;
  /** Buttons, links, focus rings — the things you click. */
  accent_color: string;
  /** The side panel's tint and other large quiet areas. */
  surface_color: string;
  /** "You are here": the active nav item, selected rows, active tabs. */
  highlight_color: string;
}

/** What the inline boot script in index.html reads. Pre-computed, so that
 *  script stays a handful of attribute writes with no maths to keep in step
 *  with this file. */
export interface CachedTheme {
  mode: string;
  font: string;
  /** `[cssCustomProperty, value]` pairs, already computed — including each
   *  colour's readable ink. A list rather than named fields so the boot script
   *  in index.html stays a loop and a fourth branded colour never needs a
   *  second edit there. */
  properties: [string, string][];
}

export const THEME_CACHE_KEY = 'second-brain.theme';

/** WCAG relative luminance. The sRGB gamma step matters: a naive average
 *  calls mid copper "light" and picks the wrong foreground. */
function relativeLuminance(hex: string): number {
  const channels = [1, 3, 5].map((start) => {
    const value = parseInt(hex.slice(start, start + 2), 16) / 255;
    return value <= 0.03928 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

function contrastRatio(luminanceA: number, luminanceB: number): number {
  const [high, low] = luminanceA > luminanceB ? [luminanceA, luminanceB] : [luminanceB, luminanceA];
  return (high + 0.05) / (low + 0.05);
}

/** The ink to write on `accent`: whichever of near-black and white is easier
 *  to read on it. Compared rather than thresholded, so there is no accent for
 *  which both are poor and neither is chosen. */
export function readableInkOn(accent: string): string {
  const dark = '#0e1118';
  const light = '#ffffff';
  if (!/^#[0-9a-f]{6}$/i.test(accent)) return dark;
  const accentLuminance = relativeLuminance(accent.toLowerCase());
  const onDark = contrastRatio(accentLuminance, relativeLuminance(dark));
  const onLight = contrastRatio(accentLuminance, relativeLuminance(light));
  return onDark >= onLight ? dark : light;
}

const DEFAULT_ACCENT = '#c58b5f';

/** The three branded colours and the custom property each one feeds. Adding a
 *  fourth is an entry here, a token in tokens.css and a swatch in Branding —
 *  nothing else, and never a second copy of the ink maths. */
const BRANDED_COLOURS: { from: keyof ThemeChoice; property: string; ink: string }[] = [
  { from: 'accent_color', property: '--color-accent', ink: '--color-on-accent' },
  { from: 'surface_color', property: '--color-brand-surface', ink: '--color-on-brand-surface' },
  { from: 'highlight_color', property: '--color-highlight', ink: '--color-on-highlight' },
];

export function applyTheme(choice: ThemeChoice): CachedTheme {
  const root = document.documentElement;
  const properties: [string, string][] = [];

  for (const { from, property, ink } of BRANDED_COLOURS) {
    const chosen = String(choice[from] ?? '');
    // An install that never set this one follows the accent, which is what
    // keeps an upgrade from repainting a rebranded sidebar in the shipped
    // copper. The backend answers the same way; this is the client-side half
    // for a response that predates the field.
    const fallback = /^#[0-9a-f]{6}$/i.test(choice.accent_color)
      ? choice.accent_color.toLowerCase()
      : DEFAULT_ACCENT;
    const colour = /^#[0-9a-f]{6}$/i.test(chosen) ? chosen.toLowerCase() : fallback;
    properties.push([property, colour], [ink, readableInkOn(colour)]);
  }

  // Dark is the stylesheet's own :root, so it is the ABSENCE of the attribute
  // rather than a value — one source of truth for "no theme chosen".
  if (choice.theme_mode === 'light') root.setAttribute('data-theme', 'light');
  else root.removeAttribute('data-theme');

  root.setAttribute('data-font', choice.font);
  for (const [property, value] of properties) root.style.setProperty(property, value);

  return { mode: choice.theme_mode, font: choice.font, properties };
}

/** Remembers the theme for the next load, so the app does not paint in the
 *  shipped dark copper for the ~100ms it takes to ask the server what this
 *  install actually looks like. Deliberately per-browser and disposable: the
 *  record on the server is the truth, this is only what spares the flash. */
export function cacheTheme(theme: CachedTheme): void {
  try {
    localStorage.setItem(THEME_CACHE_KEY, JSON.stringify(theme));
  } catch {
    // A browser with storage blocked still gets the right theme, one frame
    // later. Not worth a failure path.
  }
}
