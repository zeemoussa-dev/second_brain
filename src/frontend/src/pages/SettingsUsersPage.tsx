import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../features/auth/AuthGate';
import { refusalText } from '../features/auth/SignInScreen';
import {
  ROLE_DESCRIPTIONS,
  ROLE_LABELS,
  createUser,
  deleteUser,
  listUsers,
  setUserDisabled,
  setUserPassword,
  setUserRole,
} from '../features/auth/authApiClient';
import type { ManagedUser } from '../features/auth/authApiClient';

const ROLES: ManagedUser['role'][] = ['user', 'power_user', 'admin'];
const MINIMUM_PASSWORD_LENGTH = 8;

type Load =
  | { kind: 'loading' }
  | { kind: 'failed'; detail: string }
  | { kind: 'loaded'; users: ManagedUser[] };

/** REQ-SB-101 -- the Admin Center. Create a user, change a role, reset a
 * password, disable or delete an account.
 *
 * **Every refusal the backend gives is rendered as its own sentence.**
 * The interesting ones here are not errors in the usual sense -- "that
 * is the only active Admin", "you cannot disable your own account" --
 * and they say precisely what would have happened and what to do
 * instead. Replacing them with "Something went wrong" would remove the
 * only part worth reading.
 *
 * **This screen does not decide who may use it.** `MANAGE_USERS` is
 * enforced on the router; if a non-Admin ever reaches this page, every
 * call it makes returns 403 and it shows that. The nav simply does not
 * offer it (see SettingsPage), which is a convenience, not the control.
 */
export function SettingsUsersPage() {
  const { user: signedInUser } = useAuth();
  const [load, setLoad] = useState<Load>({ kind: 'loading' });
  const [refusal, setRefusal] = useState<string | null>(null);
  const [busyUserId, setBusyUserId] = useState<string | null>(null);

  const [newUsername, setNewUsername] = useState('');
  const [newDisplayName, setNewDisplayName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<ManagedUser['role']>('user');

  const refresh = useCallback(async () => {
    try {
      setLoad({ kind: 'loaded', users: await listUsers() });
    } catch (error) {
      setLoad({ kind: 'failed', detail: refusalText(error) });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  /** Every mutation goes through here so a refusal is shown rather than
   * swallowed, and so the list is re-read from the backend afterwards
   * instead of being patched locally -- a role change also ends that
   * user's sessions, and guessing at the new state would drift. */
  async function run(userId: string | null, work: () => Promise<unknown>) {
    setRefusal(null);
    setBusyUserId(userId);
    try {
      await work();
      await refresh();
    } catch (error) {
      setRefusal(refusalText(error));
    } finally {
      setBusyUserId(null);
    }
  }

  async function handleResetPassword(target: ManagedUser) {
    const password = window.prompt(
      `New password for ${target.username} (at least ${MINIMUM_PASSWORD_LENGTH} characters).\n\n` +
        'Their existing sessions end immediately.',
    );
    if (password === null) return;
    if (password.length < MINIMUM_PASSWORD_LENGTH) {
      setRefusal(`A password needs at least ${MINIMUM_PASSWORD_LENGTH} characters; nothing was changed.`);
      return;
    }
    await run(target.id, () => setUserPassword(target.id, password));
  }

  async function handleDelete(target: ManagedUser) {
    const confirmed = window.confirm(
      `Delete ${target.username}? This cannot be undone, and their sessions end immediately.`,
    );
    if (confirmed) await run(target.id, () => deleteUser(target.id));
  }

  if (load.kind === 'loading') {
    return <div className="settings-page"><p>Loading users…</p></div>;
  }

  if (load.kind === 'failed') {
    return (
      <div className="settings-page">
        <h1>Users</h1>
        <p className="auth-refusal" data-testid="users-load-error" role="alert">{load.detail}</p>
        <button type="button" onClick={() => void refresh()}>Try again</button>
      </div>
    );
  }

  return (
    <div className="settings-page">
      <h1>Users</h1>
      <p className="auth-note">
        Who can sign in to this install, and what each of them may do. Everyone shares
        the same vault, agents and plugins — a role decides what a person may change,
        not what they can see.
      </p>

      {refusal && (
        <p className="auth-refusal" data-testid="users-refusal" role="alert">{refusal}</p>
      )}

      <table className="settings-table" data-testid="users-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Role</th>
            <th>Status</th>
            <th>Last signed in</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {load.users.map((user) => {
            const isSelf = user.id === signedInUser.id;
            const busy = busyUserId === user.id;
            return (
              <tr key={user.id} data-testid={`user-row-${user.username}`}>
                <td>
                  {user.username}
                  {user.display_name && <span className="auth-note"> — {user.display_name}</span>}
                  {isSelf && <span className="auth-note"> (you)</span>}
                </td>
                <td>
                  <select
                    value={user.role}
                    disabled={busy}
                    aria-label={`Role for ${user.username}`}
                    onChange={(event) =>
                      void run(user.id, () =>
                        setUserRole(user.id, event.target.value as ManagedUser['role']),
                      )
                    }
                  >
                    {ROLES.map((role) => (
                      <option key={role} value={role}>{ROLE_LABELS[role]}</option>
                    ))}
                  </select>
                </td>
                <td>{user.is_disabled ? 'Disabled' : 'Active'}</td>
                <td>{user.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'Never'}</td>
                <td>
                  <button type="button" disabled={busy} onClick={() => void handleResetPassword(user)}>
                    Reset password
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void run(user.id, () => setUserDisabled(user.id, !user.is_disabled))}
                  >
                    {user.is_disabled ? 'Enable' : 'Disable'}
                  </button>
                  <button type="button" disabled={busy} onClick={() => void handleDelete(user)}>
                    Delete
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <h2>Add a user</h2>
      <form
        className="auth-card"
        data-testid="add-user-form"
        onSubmit={(event) => {
          event.preventDefault();
          void run(null, async () => {
            await createUser({
              username: newUsername,
              password: newPassword,
              role: newRole,
              display_name: newDisplayName,
            });
            setNewUsername('');
            setNewDisplayName('');
            setNewPassword('');
            setNewRole('user');
          });
        }}
      >
        <label className="auth-field">
          <span>Username</span>
          <input
            data-testid="new-user-username"
            value={newUsername}
            onChange={(event) => setNewUsername(event.target.value)}
          />
        </label>
        <label className="auth-field">
          <span>Display name <em>(optional)</em></span>
          <input
            data-testid="new-user-display-name"
            value={newDisplayName}
            onChange={(event) => setNewDisplayName(event.target.value)}
          />
        </label>
        <label className="auth-field">
          <span>Password</span>
          <input
            data-testid="new-user-password"
            type="password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
          />
          <small className="auth-hint">At least {MINIMUM_PASSWORD_LENGTH} characters.</small>
        </label>
        <label className="auth-field">
          <span>Role</span>
          <select
            data-testid="new-user-role"
            value={newRole}
            onChange={(event) => setNewRole(event.target.value as ManagedUser['role'])}
          >
            {ROLES.map((role) => (
              <option key={role} value={role}>{ROLE_LABELS[role]}</option>
            ))}
          </select>
          <small className="auth-hint">{ROLE_DESCRIPTIONS[newRole]}</small>
        </label>
        <button
          type="submit"
          className="auth-primary"
          data-testid="new-user-submit"
          disabled={!newUsername || newPassword.length < MINIMUM_PASSWORD_LENGTH}
        >
          Create user
        </button>
      </form>
    </div>
  );
}
