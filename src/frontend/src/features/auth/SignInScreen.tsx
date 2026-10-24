import { useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError } from '../../api/client';
import { signIn } from './authApiClient';
import { useBranding } from '../branding/BrandingProvider';


/** REQ-SB-101 -- the sign-in screen.
 *
 * **The backend's refusal is rendered verbatim.** It deliberately says
 * the same thing for a wrong username, a wrong password and a disabled
 * account, because distinguishing them tells an attacker which half they
 * got right. Reinterpreting it here per status code would undo that on
 * the one surface where it matters.
 */
export function SignInScreen({ onSignedIn }: { onSignedIn: () => void }) {
  const { app_name: appName, logoUrl } = useBranding();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  // Defaults ON (operator, 2026-10-24: "It Expires alot and No Remember
  // Password so I need to Enter Everything everytime"). This app runs on the
  // operator's own machine inside a closed network; being asked again every
  // morning costs them daily, and signing out still ends it everywhere.
  const [remember, setRemember] = useState(true);
  const [refusal, setRefusal] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setRefusal(null);
    setSubmitting(true);
    try {
      await signIn(username, password, remember);
      onSignedIn();
    } catch (error) {
      setRefusal(refusalText(error));
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={handleSubmit}>
      <div className="auth-brand">
        {logoUrl && <img className="auth-logo" src={logoUrl} alt="" />}
      </div>
        <h1>Sign in to {appName}</h1>

        {/* `name` and `id` are not decoration here: a password manager
            identifies a field by them, and Chrome will not offer to save a
            login whose inputs have neither -- which is why this screen had
            the right autoComplete hints and still never prompted. */}
        <label className="auth-field" htmlFor="sign-in-username">
          <span>Username</span>
          <input
            id="sign-in-username"
            name="username"
            data-testid="sign-in-username"
            autoFocus
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>

        <label className="auth-field" htmlFor="sign-in-password">
          <span>Password</span>
          <input
            id="sign-in-password"
            name="password"
            data-testid="sign-in-password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        <label className="auth-remember">
          <input
            type="checkbox"
            name="remember"
            data-testid="sign-in-remember"
            checked={remember}
            onChange={(event) => setRemember(event.target.checked)}
          />
          <span>Keep me signed in on this computer</span>
        </label>

        {refusal && (
          <p className="auth-refusal" data-testid="sign-in-refusal" role="alert">
            {refusal}
          </p>
        )}

        <button
          type="submit"
          className="auth-primary"
          data-testid="sign-in-submit"
          disabled={submitting || !username || !password}
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>

        <p className="auth-note">
          Accounts are created by an Admin, in Settings → Users.
        </p>
      </form>
    </div>
  );
}

/** An `ApiError` carries the backend's own body; anything else is the
 * request never arriving. Those are different things and the person
 * should not be told "wrong password" when the server is down. */
export function refusalText(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Second Brain could not be reached. Check that the backend is running.';
  }
  try {
    const parsed = JSON.parse(error.message) as { detail?: string };
    if (parsed.detail) return parsed.detail;
  } catch {
    // Not JSON -- fall through to the raw body, which is still the
    // backend's own words and more useful than a status code.
  }
  return error.message || `The backend answered ${error.status}.`;
}
