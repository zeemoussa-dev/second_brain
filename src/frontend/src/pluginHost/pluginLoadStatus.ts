// Whether the backend actually loaded a plugin (BUG-088).
//
// A plugin has two halves with two different gates. The backend half is
// refused at load when `framework_api` does not match exactly. The frontend
// half has no gate at all: `registry.ts` collects screens by globbing the
// folder the installer wrote, so a refused plugin keeps its routes and its
// sidebar entry, and every call its screen makes hits a prefix that was never
// mounted. The result reads as a broken page rather than a disabled plugin --
// which is what an operator sees during the window between bumping
// FRAMEWORK_API and republishing each plugin.
//
// Asked once per page load and shared: every plugin's gate wants the same
// answer, and the host does not change its mind without a backend restart.

import { useEffect, useState } from 'react';
import { apiFetch } from '../api/client';

export interface PluginLoadStatus {
  id: string;
  name: string;
  version: string;
  /** `loaded` | `refused` | `invalid` | `disabled` — the host's own vocabulary. */
  status: string;
  reason: string | null;
}

let inFlight: Promise<Map<string, PluginLoadStatus>> | null = null;

function loadStatuses(): Promise<Map<string, PluginLoadStatus>> {
  inFlight ??= apiFetch<PluginLoadStatus[]>('/plugin-host/plugins')
    .then((rows) => new Map(rows.map((row) => [row.id, row])))
    // A host that cannot be reached is not evidence that a plugin is broken:
    // an empty map means "no answer", and the gate lets the screen render
    // rather than accusing a plugin the backend never got to judge.
    .catch(() => new Map<string, PluginLoadStatus>());
  return inFlight;
}

export type GateVerdict =
  | { state: 'checking' }
  | { state: 'mount' }
  | { state: 'blocked'; status: PluginLoadStatus };

export function usePluginLoadStatus(pluginId: string): GateVerdict {
  const [verdict, setVerdict] = useState<GateVerdict>({ state: 'checking' });

  useEffect(() => {
    let abandoned = false;
    loadStatuses().then((statuses) => {
      if (abandoned) return;
      const status = statuses.get(pluginId);
      // Unknown id, or no answer at all: mount. Being absent from the report
      // is not the same as being refused, and blocking on silence would hide
      // a working screen.
      setVerdict(!status || status.status === 'loaded'
        ? { state: 'mount' }
        : { state: 'blocked', status });
    });
    return () => { abandoned = true; };
  }, [pluginId]);

  return verdict;
}
