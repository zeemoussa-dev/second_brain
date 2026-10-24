import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { apiFetch, apiUrl } from '../../api/client';
import { applyTheme, cacheTheme } from './theme';

export interface Branding {
  app_name: string;
  has_logo: boolean;
  is_customised: boolean;
  max_logo_bytes: number;
  /** This install's theme — one look for everyone, set by an Admin in
   *  Settings › Branding. Read here rather than anywhere else because
   *  `/branding` is already public and already read before sign-in: the
   *  sign-in screen has to be in the install's own colours too. */
  theme_mode: string;
  font: string;
  accent_color: string;
  surface_color: string;
  highlight_color: string;
  theme_modes: string[];
  fonts: string[];
}

export const PRODUCT_NAME = 'Second Brain';

interface BrandingContextValue extends Branding {
  /** The logo's URL, cache-busted by the moment branding was last read,
   * or null when there is none. Without the buster a browser keeps
   * showing the old logo after an upload, because the URL never
   * changes -- the one thing an operator replacing a logo would read
   * as "it did not save". */
  logoUrl: string | null;
  refresh: () => Promise<void>;
}

const FALLBACK: Branding = {
  app_name: PRODUCT_NAME,
  has_logo: false,
  is_customised: false,
  max_logo_bytes: 1024 * 1024,
  theme_mode: 'dark',
  font: 'inter',
  accent_color: '#c58b5f',
  surface_color: '#c58b5f',
  highlight_color: '#c58b5f',
  theme_modes: ['dark', 'light'],
  fonts: ['inter', 'plex', 'source'],
};

const BrandingContext = createContext<BrandingContextValue>({
  ...FALLBACK,
  logoUrl: null,
  refresh: async () => {},
});

export function useBranding(): BrandingContextValue {
  return useContext(BrandingContext);
}

/** This install's own name and logo, read once and shared.
 *
 * Wraps AuthGate rather than sitting inside it: the sign-in and
 * first-Admin screens show the name and logo, so branding has to be
 * known before anyone is identified. `/branding` is public for exactly
 * this reason.
 *
 * **Never blocks rendering and never shows an error.** If the read
 * fails the product's own name is used, which is visibly the default
 * and therefore self-reporting. Branding is decoration: an install that
 * cannot read it must still be usable, and a full-screen "could not
 * load branding" would be a worse failure than the wrong word in the
 * sidebar.
 */
export function BrandingProvider({ children }: { children: ReactNode }) {
  const [branding, setBranding] = useState<Branding>(FALLBACK);
  const [readAt, setReadAt] = useState(() => Date.now());

  const refresh = useCallback(async () => {
    try {
      setBranding(await apiFetch<Branding>('/branding'));
    } catch {
      setBranding(FALLBACK);
    } finally {
      setReadAt(Date.now());
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // The tab title follows the install's name too -- someone with this
  // app open beside three others reads the tab, not the sidebar.
  useEffect(() => {
    document.title = branding.app_name;
  }, [branding.app_name]);

  // The theme is applied here and nowhere else: one place that writes
  // data-theme/data-font/--color-accent means a screen can never set its own
  // and disagree with the rest of the app. Caching it is what lets the next
  // load paint in these colours instead of the shipped ones (index.html).
  useEffect(() => {
    cacheTheme(
      applyTheme({
        theme_mode: branding.theme_mode,
        font: branding.font,
        accent_color: branding.accent_color,
        surface_color: branding.surface_color,
        highlight_color: branding.highlight_color,
      }),
    );
  }, [
    branding.theme_mode,
    branding.font,
    branding.accent_color,
    branding.surface_color,
    branding.highlight_color,
  ]);

  const value: BrandingContextValue = {
    ...branding,
    logoUrl: branding.has_logo ? apiUrl(`/branding/logo?v=${readAt}`) : null,
    refresh,
  };
  return <BrandingContext.Provider value={value}>{children}</BrandingContext.Provider>;
}
