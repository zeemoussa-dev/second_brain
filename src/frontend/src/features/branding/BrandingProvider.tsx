import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { apiFetch, apiUrl } from '../../api/client';

export interface Branding {
  app_name: string;
  has_logo: boolean;
  is_customised: boolean;
  max_logo_bytes: number;
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

  const value: BrandingContextValue = {
    ...branding,
    logoUrl: branding.has_logo ? apiUrl(`/branding/logo?v=${readAt}`) : null,
    refresh,
  };
  return <BrandingContext.Provider value={value}>{children}</BrandingContext.Provider>;
}
