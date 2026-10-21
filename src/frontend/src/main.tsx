import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/tokens.css'
import './styles/shell.css'
import './styles/markdown.css'
import './styles/settings.css'
import './styles/agents-map.css'
import './styles/my-day.css'
import './styles/agent-panel.css'
import './styles/vault-browser.css'
import './styles/vault-graph.css'
import './styles/cockpit.css'
import './styles/boot.css'
import './styles/setup.css'
import './styles/auth.css'
import App from './App.tsx'
import { AuthGate } from './features/auth/AuthGate.tsx'
import { BrandingProvider } from './features/branding/BrandingProvider.tsx'
import { BootGate } from './features/boot/BootGate.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/* Boot first, then identity (REQ-SB-101). AuthGate sits INSIDE
        BootGate because an install that cannot boot has nothing to sign
        in to, and a password form in front of a broken backend replaces
        a useful boot error with one that cannot succeed. */}
    <BootGate>
      {/* Branding wraps AuthGate: the sign-in and first-Admin screens
          render this install's name and logo, so it must be known
          before anyone is identified. */}
      <BrandingProvider>
        <AuthGate>
          <App />
        </AuthGate>
      </BrandingProvider>
    </BootGate>
  </StrictMode>,
)
