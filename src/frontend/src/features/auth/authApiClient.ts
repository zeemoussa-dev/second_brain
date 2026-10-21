import { apiFetch } from '../../api/client';

/** Who the signed-in person is, and what their role lets them do
 * (REQ-SB-101). `capabilities` is sent by the backend rather than derived
 * here from the role: the matrix lives in one place on the server, and a
 * second copy in the frontend would be the thing that goes stale when the
 * operator corrects it. */
export interface SignedInUser {
  id: string;
  username: string;
  display_name: string;
  role: 'user' | 'power_user' | 'admin';
  capabilities: string[];
  last_login_at: string | null;
}

/** The three states the app can be in before it shows anything.
 *
 * `needs_bootstrap` is deliberately separate from `signed_in`: an install
 * with no accounts at all is not "signed out", and sending a new operator
 * to a login form they cannot possibly satisfy is the failure this
 * distinction exists to prevent. */
export interface AuthState {
  needs_bootstrap: boolean;
  signed_in: boolean;
  user: SignedInUser | null;
}

export function fetchAuthState(): Promise<AuthState> {
  return apiFetch<AuthState>('/auth/state');
}

export function signIn(username: string, password: string): Promise<{ user: SignedInUser }> {
  return apiFetch<{ user: SignedInUser }>('/auth/sign-in', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export function signOut(): Promise<{ signed_out: boolean }> {
  return apiFetch<{ signed_out: boolean }>('/auth/sign-out', { method: 'POST' });
}

export function bootstrapFirstAdmin(
  username: string,
  password: string,
  displayName: string,
): Promise<{ user: SignedInUser }> {
  return apiFetch<{ user: SignedInUser }>('/auth/bootstrap', {
    method: 'POST',
    body: JSON.stringify({ username, password, display_name: displayName }),
  });
}

// ---- the Admin Center -------------------------------------------------

export interface ManagedUser {
  id: string;
  username: string;
  display_name: string;
  role: SignedInUser['role'];
  is_disabled: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export function listUsers(): Promise<ManagedUser[]> {
  return apiFetch<ManagedUser[]>('/admin/users');
}

export function createUser(body: {
  username: string;
  password: string;
  role: ManagedUser['role'];
  display_name: string;
}): Promise<ManagedUser> {
  return apiFetch<ManagedUser>('/admin/users', { method: 'POST', body: JSON.stringify(body) });
}

export function setUserRole(userId: string, role: ManagedUser['role']): Promise<ManagedUser> {
  return apiFetch<ManagedUser>(`/admin/users/${userId}/role`, {
    method: 'PUT',
    body: JSON.stringify({ role }),
  });
}

export function setUserDisabled(userId: string, isDisabled: boolean): Promise<ManagedUser> {
  return apiFetch<ManagedUser>(`/admin/users/${userId}/disabled`, {
    method: 'PUT',
    body: JSON.stringify({ is_disabled: isDisabled }),
  });
}

export function setUserPassword(userId: string, password: string): Promise<{ password_set: boolean }> {
  return apiFetch<{ password_set: boolean }>(`/admin/users/${userId}/password`, {
    method: 'PUT',
    body: JSON.stringify({ password }),
  });
}

export function deleteUser(userId: string): Promise<void> {
  return apiFetch<void>(`/admin/users/${userId}`, { method: 'DELETE' });
}

export const ROLE_LABELS: Record<ManagedUser['role'], string> = {
  user: 'User',
  power_user: 'Power User',
  admin: 'Admin',
};

/** What each role may do, in the words the Admin Center shows beside it.
 * A description, never a check -- every real decision is the backend's,
 * and this is here so an Admin choosing a role can see what they are
 * granting rather than having to remember. */
export const ROLE_DESCRIPTIONS: Record<ManagedUser['role'], string> = {
  user: 'Reads the vault, chats with agents, uses plugin screens.',
  power_user: 'Everything a User can do, plus running actions and workflows, confirming them, reading agent transcripts and rebuilding the index.',
  admin: 'Everything, including authoring actions and workflows, plugins, settings, Hermes and managing users.',
};

// ---- your own account -------------------------------------------------

export function updateMyProfile(displayName: string): Promise<SignedInUser> {
  return apiFetch<SignedInUser>('/auth/me', {
    method: 'PUT',
    body: JSON.stringify({ display_name: displayName }),
  });
}

/** Changing your own password requires your current one — an Admin's
 * reset of someone else's does not. Every other session of yours ends;
 * the one you are using survives. */
export function changeMyPassword(
  currentPassword: string,
  newPassword: string,
): Promise<{ password_changed: boolean }> {
  return apiFetch<{ password_changed: boolean }>('/auth/me/password', {
    method: 'PUT',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
}
