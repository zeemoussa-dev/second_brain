import { useNavigate } from 'react-router';
import { SetupWizard } from '../features/setup/SetupWizard';

/** REQ-SB-89 -- the wizard's on-demand entry point (/setup), reachable from
 * Settings so it can be re-run deliberately without deleting .env first
 * (operator's own choice over a purely-automatic trigger). BootGate renders
 * the same component automatically when the backend reports setup_required;
 * the only difference here is that leaving is allowed, since the app behind
 * it is already working. */
export function SetupPage() {
  const navigate = useNavigate();
  return <SetupWizard onDismiss={() => navigate('/settings/system')} />;
}
