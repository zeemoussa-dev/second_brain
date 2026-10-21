import { useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../features/auth/AuthGate';
import { initialsFor } from '../components/shell/SignedInAs';
import { refusalText } from '../features/auth/SignInScreen';
import {
  ROLE_DESCRIPTIONS,
  ROLE_LABELS,
  changeMyPassword,
  updateMyProfile,
} from '../features/auth/authApiClient';

const MINIMUM_PASSWORD_LENGTH = 8;

/** Turns a capability name into the words the matrix uses for it, so a
 * person reading their own profile sees what they may do rather than a
 * list of identifiers. An unknown key renders as itself: the backend is
 * the source of the list, and a capability added there should show up
 * here imperfectly rather than vanish. */
const CAPABILITY_LABELS: Record<string, string> = {
  read_vault: 'Read the vault',
  chat_with_agents: 'Chat with agents',
  use_plugin_screens: 'Use plugin screens',
  resolve_entities: 'Look up entities',
  view_agents: 'View agents',
  read_agent_transcripts: 'Read agent transcripts',
  call_actions: 'Call actions',
  confirm_actions: 'Confirm actions that need a human',
  run_workflows: 'Run workflows',
  rebuild_vault_index: 'Rebuild the vault index',
  author_automations: 'Author actions and workflows',
  manage_agents: 'Create and edit agents',
  manage_plugins: 'Install and remove plugins',
  manage_settings: 'Change settings',
  manage_hermes: 'Configure Hermes',
  export_and_backup: 'Export and back up',
  manage_operator_profile: 'Edit the Operator Profile',
  manage_users: 'Manage users',
};

/** REQ-SB-101 -- your own account: who you are signed in as, what your
 * role lets you do, your display name, and your password.
 *
 * **Not the Operator Profile.** That is a different record at
 * Settings → Operator: who this install's AGENTS act for, shared by
 * everyone, and Admin-only. This page is one person's own account on a
 * shared install. The two are named similarly enough that the page says
 * so out loud rather than leaving someone to discover they edited the
 * wrong one.
 *
 * **It shows the capability list rather than just the role name.**
 * "Power User" means nothing on its own, and the one question this page
 * exists to answer is "why can't I do X" -- which a role name cannot
 * answer and a list of what you may do can.
 */
export function ProfilePage() {
  const { user, refresh } = useAuth();

  const [displayName, setDisplayName] = useState(user.display_name);
  const [nameRefusal, setNameRefusal] = useState<string | null>(null);
  const [nameSaved, setNameSaved] = useState(false);
  const [savingName, setSavingName] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordRefusal, setPasswordRefusal] = useState<string | null>(null);
  const [passwordChanged, setPasswordChanged] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  async function handleNameSubmit(event: FormEvent) {
    event.preventDefault();
    setNameRefusal(null);
    setNameSaved(false);
    setSavingName(true);
    try {
      await updateMyProfile(displayName);
      // Re-read rather than patch locally: the sidebar renders the same
      // user, and two copies drifting is how a name change half-applies.
      await refresh();
      setNameSaved(true);
    } catch (error) {
      setNameRefusal(refusalText(error));
    } finally {
      setSavingName(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setPasswordRefusal(null);
    setPasswordChanged(false);
    setChangingPassword(true);
    try {
      await changeMyPassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setPasswordChanged(true);
    } catch (error) {
      setPasswordRefusal(refusalText(error));
    } finally {
      setChangingPassword(false);
    }
  }

  return (
    <div className="settings-page profile-page">
      <h1>Your profile</h1>

      <section className="profile-identity" data-testid="profile-identity">
        <span className="profile-avatar" aria-hidden="true">
          {initialsFor(user.display_name, user.username)}
        </span>
        <div>
          <p className="profile-name">{user.display_name || user.username}</p>
          <p className="auth-note">
            Signed in as <strong>{user.username}</strong> · {ROLE_LABELS[user.role]}
          </p>
          <p className="auth-note">
            {user.last_login_at
              ? `Last signed in ${new Date(user.last_login_at).toLocaleString()}.`
              : 'This is your first sign-in.'}
          </p>
        </div>
      </section>

      <p className="auth-note">
        This is your own account. <strong>Settings → Operator</strong> is a different
        record — who this install's agents act for — shared by everyone here.
      </p>

      <section>
        <h2>What your role lets you do</h2>
        <p className="auth-note">{ROLE_DESCRIPTIONS[user.role]}</p>
        <ul className="profile-capabilities" data-testid="profile-capabilities">
          {user.capabilities.map((capability) => (
            <li key={capability}>{CAPABILITY_LABELS[capability] ?? capability}</li>
          ))}
        </ul>
        <p className="auth-note">
          Only an Admin can change your role. If something you need is missing, ask one.
        </p>
      </section>

      <section>
        <h2>Display name</h2>
        <form className="auth-card" onSubmit={handleNameSubmit} data-testid="profile-name-form">
          <label className="auth-field">
            <span>How your name appears in this app</span>
            <input
              data-testid="profile-display-name"
              value={displayName}
              onChange={(event) => {
                setDisplayName(event.target.value);
                setNameSaved(false);
              }}
            />
            <small className="auth-hint">
              Your username, <strong>{user.username}</strong>, is what you sign in with and
              cannot be changed here — ask an Admin.
            </small>
          </label>
          {nameRefusal && (
            <p className="auth-refusal" role="alert" data-testid="profile-name-refusal">{nameRefusal}</p>
          )}
          {nameSaved && <p className="profile-done" role="status">Saved.</p>}
          <button
            type="submit"
            className="auth-primary"
            data-testid="profile-name-submit"
            disabled={savingName || displayName === user.display_name}
          >
            {savingName ? 'Saving…' : 'Save display name'}
          </button>
        </form>
      </section>

      <section>
        <h2>Password</h2>
        <form className="auth-card" onSubmit={handlePasswordSubmit} data-testid="profile-password-form">
          <label className="auth-field">
            <span>Current password</span>
            <input
              data-testid="profile-current-password"
              type="password"
              autoComplete="current-password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </label>
          <label className="auth-field">
            <span>New password</span>
            <input
              data-testid="profile-new-password"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
            <small className="auth-hint">At least {MINIMUM_PASSWORD_LENGTH} characters.</small>
          </label>
          {passwordRefusal && (
            <p className="auth-refusal" role="alert" data-testid="profile-password-refusal">
              {passwordRefusal}
            </p>
          )}
          {passwordChanged && (
            <p className="profile-done" role="status" data-testid="profile-password-done">
              Password changed. You are still signed in here; anywhere else you were signed
              in has been signed out.
            </p>
          )}
          <p className="auth-note">
            Your current password is required — without it, anyone who picked up an open
            session of yours could lock you out of your own account.
          </p>
          <button
            type="submit"
            className="auth-primary"
            data-testid="profile-password-submit"
            disabled={
              changingPassword || !currentPassword || newPassword.length < MINIMUM_PASSWORD_LENGTH
            }
          >
            {changingPassword ? 'Changing…' : 'Change password'}
          </button>
        </form>
      </section>
    </div>
  );
}
