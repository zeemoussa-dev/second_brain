import { useRef, useState } from 'react';
import type { ChangeEvent, FormEvent } from 'react';
import { apiFetch, apiUrl } from '../api/client';
import { refusalText } from '../features/auth/SignInScreen';
import { PRODUCT_NAME, useBranding } from '../features/branding/BrandingProvider';
import type { Branding } from '../features/branding/BrandingProvider';

/** The copy for each font the backend offers. Keyed by the id it stores; the
 *  stylesheet owns the real stack, and `stack` here is only what renders this
 *  one button in its own face. */
const FONTS: Record<string, { name: string; stack: string; note: string }> = {
  inter: {
    name: 'Inter',
    stack: '"Inter", "Segoe UI", sans-serif',
    note: 'Neutral, dense, built for screens',
  },
  plex: {
    name: 'IBM Plex Sans',
    stack: '"IBM Plex Sans", "Segoe UI", sans-serif',
    note: 'Technical, a little more formal',
  },
  source: {
    name: 'Source Sans 3',
    stack: '"Source Sans 3", "Segoe UI", sans-serif',
    note: 'Open and plain, easy at small sizes',
  },
};

const DEFAULT_ACCENT = '#c58b5f';

/** The three branded colours, and the job each one does — the labels say what
 *  changes on screen, because "accent" and "highlight" mean nothing until you
 *  know which of them moves the sidebar. */
type ColourRole = 'accent_color' | 'surface_color' | 'highlight_color';

const COLOUR_ROLES: { key: ColourRole; label: string; note: string }[] = [
  {
    key: 'accent_color',
    label: 'Action',
    note: 'The things you click: buttons, links, focus rings. This one may be loud.',
  },
  {
    key: 'surface_color',
    label: 'Surface',
    note: 'The side panel and other large quiet areas. Used as a faint tint, not a fill — a colour strong enough for a button covers a whole sidebar badly.',
  },
  {
    key: 'highlight_color',
    label: 'Highlight',
    note: '"You are here": the active item in the side panel, selected rows, active tabs. Keep it distinguishable from the other two or the marker stops reading as one.',
  },
];

/** This install's own name, logo and theme (operator, 2026-10-21, 2026-10-24).
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
  // Held locally so a colour picker can be dragged without a PUT per frame;
  // the saved values are still the ones on `branding` until Save is pressed.
  const [colours, setColours] = useState<Record<ColourRole, string>>({
    accent_color: branding.accent_color,
    surface_color: branding.surface_color,
    highlight_color: branding.highlight_color,
  });

  function setColour(role: ColourRole, value: string) {
    setColours((previous) => ({ ...previous, [role]: value }));
  }
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

  function handleTheme(patch: Record<string, string>, message: string) {
    void run(
      () => apiFetch<Branding>('/branding/theme', { method: 'PUT', body: JSON.stringify(patch) }),
      message,
    );
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
        <h2>Theme</h2>
        <p className="auth-note">
          One look for the whole install, like the name and the logo — not a personal
          setting. It applies the moment you save, on every screen and for everyone.
        </p>
        <div className="auth-card">
          <div className="branding-choice-group" data-testid="branding-mode">
            <span className="branding-choice-label">Mode</span>
            <div className="branding-choices">
              {branding.theme_modes.map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`branding-choice ${branding.theme_mode === mode ? 'is-chosen' : ''}`}
                  aria-pressed={branding.theme_mode === mode}
                  disabled={busy}
                  onClick={() => handleTheme({ theme_mode: mode }, `Switched to the ${mode} theme.`)}
                >
                  <span className="material-symbols-outlined" aria-hidden="true">
                    {mode === 'light' ? 'light_mode' : 'dark_mode'}
                  </span>
                  {mode === 'light' ? 'Light' : 'Dark'}
                </button>
              ))}
            </div>
          </div>

          <div className="branding-choice-group" data-testid="branding-font">
            <span className="branding-choice-label">Font</span>
            <div className="branding-choices">
              {branding.fonts.map((font) => {
                const face = FONTS[font];
                if (!face) return null;
                return (
                  <button
                    key={font}
                    type="button"
                    className={`branding-choice branding-font-choice ${branding.font === font ? 'is-chosen' : ''}`}
                    aria-pressed={branding.font === font}
                    disabled={busy}
                    // Rendered in its own face: the only honest way to choose a
                    // font is to read it.
                    style={{ fontFamily: face.stack }}
                    onClick={() => handleTheme({ font }, `Now set in ${face.name}.`)}
                  >
                    <strong>{face.name}</strong>
                    <small>{face.note}</small>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="branding-colour-grid">
          {COLOUR_ROLES.map((role) => (
            <div className="branding-choice-group" key={role.key}>
              <span className="branding-choice-label">{role.label}</span>
              <div className="branding-accent-row">
                <input
                  type="color"
                  className="branding-accent-swatch"
                  data-testid={`branding-${role.key}-picker`}
                  value={colours[role.key]}
                  disabled={busy}
                  onChange={(event) => setColour(role.key, event.target.value)}
                  aria-label={role.label}
                />
                <input
                  className="input branding-accent-hex"
                  data-testid={`branding-${role.key}-hex`}
                  value={colours[role.key]}
                  maxLength={7}
                  spellCheck={false}
                  disabled={busy}
                  onChange={(event) => setColour(role.key, event.target.value)}
                />
                <button
                  type="button"
                  className="auth-primary"
                  data-testid={`branding-${role.key}-save`}
                  disabled={busy || colours[role.key].toLowerCase() === branding[role.key].toLowerCase()}
                  onClick={() => handleTheme({ [role.key]: colours[role.key] }, `${role.label} saved.`)}
                >
                  Save
                </button>
                {/* Back to following the Action colour, which is what an
                    install that never set this one already does. */}
                {role.key !== 'accent_color' &&
                  branding[role.key].toLowerCase() !== branding.accent_color.toLowerCase() && (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => {
                        setColour(role.key, branding.accent_color);
                        handleTheme(
                          { [role.key]: branding.accent_color },
                          `${role.label} follows the action colour again.`,
                        );
                      }}
                    >
                      Match action
                    </button>
                  )}
                {role.key === 'accent_color' && branding.accent_color.toLowerCase() !== DEFAULT_ACCENT && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      setColour('accent_color', DEFAULT_ACCENT);
                      handleTheme({ accent_color: DEFAULT_ACCENT }, 'Back to the default colour.');
                    }}
                  >
                    Reset
                  </button>
                )}
              </div>
              <small className="auth-hint">{role.note}</small>
            </div>
          ))}
          </div>
          <p className="auth-hint">
            The text colour on top of each is worked out from the colour you pick, so a
            pale one gets dark text rather than white on white. Set them all the same and
            the app looks exactly as it does with one colour.
          </p>
        </div>
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
