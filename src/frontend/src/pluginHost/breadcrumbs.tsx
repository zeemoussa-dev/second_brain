import { useSearchParams } from 'react-router';
import { Breadcrumbs, type Crumb } from '../components/Breadcrumbs';
import { belongsToPlugin, pluginNavEntries } from './registry';
import type { MountedSettingsPage } from './types';

export { Breadcrumbs } from '../components/Breadcrumbs';
export type { Crumb, BreadcrumbsProps } from '../components/Breadcrumbs';

/** Where a link into Settings came from. Carried in the URL so it survives a
 *  refresh and a shared address, like every other piece of "what you are
 *  looking at" since v10. */
const RETURN_PATH_PARAM = 'back';
const RETURN_LABEL_PARAM = 'backLabel';

export interface PluginSettingsLinkOptions {
  /** A settings sub-page, relative to `/settings/plugins/<plugin-id>`. */
  page?: string;
  /** Extra query parameters for the settings page itself. */
  params?: Record<string, string>;
  /** Where the operator is now -- pass `useLocation()`. */
  from?: { pathname: string; search?: string };
  /** What to call that place in the trail, e.g. a customer's name. */
  fromLabel?: string;
}

/**
 * A link into one of this plugin's Settings pages that remembers where it was
 * opened from, so the trail reads "Azure Cost › ADNOC › Customers" and Save or
 * Cancel can return there.
 *
 * Settings lives under the HOST's `/settings`, a different top-level area from
 * the plugin's own screens, so the sidebar cannot lead back: without this the
 * operator arrives with no way out (the real complaint, 2026-10-17).
 */
export function pluginSettingsLink(pluginId: string, options: PluginSettingsLinkOptions = {}): string {
  const relativePage = (options.page ?? '').replace(/^\/+|\/+$/g, '');
  const base = relativePage
    ? `/settings/plugins/${pluginId}/${relativePage}`
    : `/settings/plugins/${pluginId}`;

  const search = new URLSearchParams(options.params ?? {});
  if (options.from) {
    search.set(RETURN_PATH_PARAM, `${options.from.pathname}${options.from.search ?? ''}`);
    if (options.fromLabel) search.set(RETURN_LABEL_PARAM, options.fromLabel);
  }
  const query = search.toString();
  return query ? `${base}?${query}` : base;
}

/**
 * A `back` path from the URL, or null -- validated to be one of THIS plugin's
 * own screens by the same rule that decides which routes it may mount.
 *
 * The validation is the host's job precisely because it is a security check: a
 * plugin that forgot it, or wrote a looser pattern than
 * `belongsToPlugin`, would let a crafted link bounce the operator anywhere in
 * the app (or, with a protocol-relative path, off it entirely).
 */
export function returnPathFor(pluginId: string, rawPath: string | null): string | null {
  if (!rawPath || !rawPath.startsWith('/') || rawPath.startsWith('//')) return null;
  const [pathname] = rawPath.split(/[?#]/);
  return belongsToPlugin(pluginId, pathname) ? rawPath : null;
}

export interface PluginReturn {
  to: string;
  label: string;
}

/**
 * Where this Settings page should lead back to, when it was opened from one of
 * the plugin's own screens. Null when it was reached from Settings itself --
 * then there is nothing to return to and no crumb to show.
 *
 * Use it for Save and Cancel; the trail above the page is already rendered by
 * the host, so a plugin never parses these parameters itself.
 */
export function usePluginReturn(pluginId: string): PluginReturn | null {
  const [params] = useSearchParams();
  const to = returnPathFor(pluginId, params.get(RETURN_PATH_PARAM));
  if (!to) return null;
  return { to, label: params.get(RETURN_LABEL_PARAM)?.trim() || 'Back' };
}

/** The plugin's landing page -- its first sidebar entry, which is the screen
 *  its nav leads to. Falls back to `/<plugin-id>` for a plugin that contributes
 *  screens but no sidebar entry. */
function landingCrumb(pluginId: string) {
  const entry = pluginNavEntries.find((navEntry) => navEntry.pluginId === pluginId);
  return { label: entry?.label ?? pluginId, to: entry?.to ?? `/${pluginId}` };
}

/**
 * The trail the HOST renders above a plugin's Settings page: the plugin's
 * landing page, then wherever the link was opened from, then this page.
 *
 * Rendered by the host rather than by each plugin because a Settings page sits
 * under `/settings`, which the plugin does not own and cannot describe.
 */
export function PluginSettingsTrail({ page }: { page: MountedSettingsPage }) {
  const origin = usePluginReturn(page.pluginId);
  // Typed, not inferred: inferred from its first element the array becomes
  // `{ label, to }[]`, and the current page -- which has no `to` -- cannot be
  // pushed onto it.
  const items: Crumb[] = [landingCrumb(page.pluginId)];
  if (origin) items.push({ label: origin.label, to: origin.to });
  items.push({ label: page.label });
  return <Breadcrumbs items={items} />;
}
