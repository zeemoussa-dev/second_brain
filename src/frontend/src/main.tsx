import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/tokens.css'
import './styles/shell.css'
import './styles/settings.css'
import './styles/agents-map.css'
import './styles/my-day.css'
import './styles/agent-panel.css'
import './styles/vault-browser.css'
import './styles/vault-graph.css'
import './styles/cockpit.css'
import './styles/boot.css'
import App from './App.tsx'
import { BootGate } from './features/boot/BootGate.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BootGate>
      <App />
    </BootGate>
  </StrictMode>,
)
