import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      // Publishing a plugin, and installing one, prove its screens compile by
      // copying them to `src/plugins/__<purpose>-check-<id>/` and building the
      // whole frontend (`screen_build.py`). The copy has to sit at an installed
      // plugin's depth so `../../pluginHost/...` resolves, which puts it inside
      // the tree this dev server watches: appearing and then vanishing, it was
      // hot-reloaded into whatever page the operator had open, and its removal
      // filled their console with "[vite] Failed to reload" and 404s
      // (reported live 2026-10-17). Ignored here rather than moved out of
      // `src/`, so the gate still builds the screens exactly where they will
      // run. Vite concatenates this with its own defaults, so node_modules and
      // .git stay ignored too.
      ignored: ['**/src/plugins/__*-check-*/**'],
    },
  },
})
