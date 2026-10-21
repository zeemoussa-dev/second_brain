import { useRef, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { apiFetch, apiUrl } from '../api/client';
import { refusalText } from '../features/auth/SignInScreen';
import { PRODUCT_NAME, useBranding } from '../features/branding/BrandingProvider';
import type { Branding } from '../features/branding/BrandingProvider';

/** This install's own name and logo (operator, 2026-10-21).
 *
 * Admin-only, by `MANAGE_SETTINGS` on the routes — this is what
 * everyone else on the install sees, so it is closer to a setting than
 * to a personal preference.
 *
 * **Every refusal the backend gives is rendered verbatim**, and here
 * they are the interesting part: a file named `.png` that is not a PNG,
 * an SVG carrying a script, a name too long for the sidebar. Each one
 * says what was wrong and that nothing was changed, which "Upload
 * failed" would not.
 */
export function SettingsBrandingPage() {
  const branding = useBranding();
  const [name, setName] = useState(branding.is_customised ? branding.app_name : '');
  const [refusal, setRefusal] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  async function run(work: () => Promise<unknown>, message: string) {
    setRefusal(null);
    setDone(null);
    setBusy(true);
    try {
      await work();
      // Re-read through the provider so the sidebar, the tab title and
      // this page all move together; patching locally would leave the
      // sidebar showing the old name until a reload.
      await branding.refresh();
      setDone(message);
    } catch (error) {
      setRefusal(refusalText(error));
    } finally {
      setBusy(false);
    }
  }

  function handleName(event: FormEvent) {
    event.preventDefault();
    void run(
      () => apiFetch<Branding>('/branding', { method: 'PUT', body: JSON.stringify({ app_name: name }) }),
      name.trim() ? 'Name saved.' : `Reset to ${PRODUCT_NAME}.`,
    );
  }

  function handleLogo(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const body = new FormData();
    body.append('file', file);
    // No Content-Type header: apiFetch leaves a FormData body alone so
    // the browser sets its own multipart boundary.
    void run(() => apiFetch<Branding>('/branding/logo', { method: 'POST', body }), 'Logo uploaded.');
    if (fileInput.current) fileInput.current.value = '';
  }

  const limitKb = Math.round(branding.max_logo_bytes / 1024);

  return (
    <div className="settings-page">
      <h1>Branding</h1>
      <p className="auth-note">
        What this install calls itself, and the logo beside it. Shown in the sidebar, in
        the browser tab, and on the sign-in screen — so everyone here sees it, signed in
        or not.
      </p>

      {refusal && <p className="auth-refusal" role="alert" data-testid="branding-refusal">{refusal}</p>}
      {done && <p className="profile-done" role="status" data-testid="branding-done">{done}</p>}

      <section>
        <h2>Name</h2>
        <form className="auth-card" onSubmit={handleName} data-testid="branding-name-form">
          <label className="auth-field">
            <span>App name</span>
            <input
              data-testid="branding-name"
              value={name}
              placeholder={PRODUCT_NAME}
              maxLength={60}
              onChange={(event) => setName(event.target.value)}
            />
            <small className="auth-hint">
              Leave it empty to go back to {PRODUCT_NAME}. Up to 60 characters — it has to
              fit the sidebar and a browser tab.
            </small>
          </label>
          <button type="submit" className="auth-primary" data-testid="branding-name-submit" disabled={busy}>
            {busy ? 'Saving…' : 'Save name'}
          </button>
        </form>
      </section>

      <section>
        <h2>Logo</h2>
        <div className="auth-card">
          <div className="branding-logo-preview" data-testid="branding-logo-preview">
            {branding.logoUrl ? (
              <img src={branding.logoUrl} alt={`${branding.app_name} logo`} />
            ) : (
              <p className="auth-note">No logo set — the name shows on its own.</p>
            )}
          </div>
          <label className="auth-field">
            <span>Replace the logo</span>
            <input
              ref={fileInput}
              data-testid="branding-logo-file"
              type="file"
              accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
              onChange={handleLogo}
              disabled={busy}
            />
            <small className="auth-hint">
              PNG, JPEG, GIF, WebP or SVG, up to {limitKb} KB. A square image reads best
              beside the name. An SVG containing a script is refused — it would be
              rendered as a document on every page.
            </small>
          </label>
          {branding.has_logo && (
            <button
              type="button"
              data-testid="branding-logo-clear"
              disabled={busy}
              onClick={() => void run(
                () => apiFetch<Branding>('/branding/logo', { method: 'DELETE' }),
                'Logo removed.',
              )}
            >
              Remove logo
            </button>
          )}
          <p className="auth-note">
            Stored on this machine, in the config folder — a logo is this install's own
            and never travels in an export or a backup.{' '}
            <a href={apiUrl('/branding/logo')} target="_blank" rel="noreferrer">
              {branding.has_logo ? 'Open the stored file' : ''}
            </a>
          </p>
        </div>
      </section>
    </div>
  );
}
