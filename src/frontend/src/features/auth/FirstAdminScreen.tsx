import { useState } from 'react';
import type { FormEvent } from 'react';
import { bootstrapFirstAdmin } from './authApiClient';
import { refusalText } from './SignInScreen';
import { useBranding } from '../branding/BrandingProvider';


const MINIMUM_PASSWORD_LENGTH = 8;

/** REQ-SB-101 -- the one-time first-Admin screen, shown only while this
 * install has no accounts at all.
 *
 * **It says what it is giving away.** Whoever fills this in becomes the
 * Admin of an install that already holds the operator's vault, mail and
 * agents, and the window closes the moment the account exists. That is
 * worth one sentence on the screen rather than being something the
 * person discovers afterwards.
 *
 * There is no password-confirm field. A typo here is recoverable in the
 * one way that matters -- this account can reset its own password from
 * the Admin Center once signed in -- and a confirm field on a form
 * nobody can be locked out of is friction without a benefit.
 */
export function FirstAdminScreen({ onBootstrapped }: { onBootstrapped: () => void }) {
  const { logoUrl } = useBranding();
  const [username, setUsername] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [password, setPassword] = useState('');
  const [refusal, setRefusal] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const tooShort = password.length > 0 && password.length < MINIMUM_PASSWORD_LENGTH;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setRefusal(null);
    setSubmitting(true);
    try {
      await bootstrapFirstAdmin(username, password, displayName);
      onBootstrapped();
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
        <h1>Create the first Admin</h1>
        <p className="auth-note" data-testid="first-admin-explainer">
          This install has no accounts yet. The account you create here becomes its
          Admin — able to manage users, settings, plugins and Hermes — and this screen
          closes as soon as it exists.
        </p>

        <label className="auth-field">
          <span>Username</span>
          <input
            data-testid="first-admin-username"
            autoFocus
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>

        <label className="auth-field">
          <span>Display name <em>(optional)</em></span>
          <input
            data-testid="first-admin-display-name"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
          />
        </label>

        <label className="auth-field">
          <span>Password</span>
          <input
            data-testid="first-admin-password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <small className={tooShort ? 'auth-hint-warn' : 'auth-hint'}>
            At least {MINIMUM_PASSWORD_LENGTH} characters.
          </small>
        </label>

        {refusal && (
          <p className="auth-refusal" data-testid="first-admin-refusal" role="alert">
            {refusal}
          </p>
        )}

        <button
          type="submit"
          className="auth-primary"
          data-testid="first-admin-submit"
          disabled={submitting || !username || password.length < MINIMUM_PASSWORD_LENGTH}
        >
          {submitting ? 'Creating…' : 'Create Admin and sign in'}
        </button>
      </form>
    </div>
  );
}
