import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { ApiError } from '../../api/client';
import { fetchAuthState, signOut as signOutRequest } from './authApiClient';
import type { AuthState, SignedInUser } from './authApiClient';
import { FirstAdminScreen } from './FirstAdminScreen';
import { SignInScreen } from './SignInScreen';


/** The signed-in person, for anything that needs to know who they are or
 * what they may do. Never null inside the gate: the gate does not render
 * its children until there is a user, so a consumer can read
 * `user.role` without a guard. */
interface AuthContextValue {
  user: SignedInUser;
  signOut: () => Promise<void>;
  may: (capability: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth was called outside AuthGate');
  return value;
}

/** True when the signed-in person has the capability. Asks the context
 * rather than comparing roles: a screen that hides a button when
 * `role === 'admin'` is false has to be found and changed every time the
 * matrix moves, and the matrix is the operator's to correct. */
export function useMay(capability: string): boolean {
  return useAuth().may(capability);
}

type Phase =
  | { kind: 'loading' }
  | { kind: 'unreachable'; detail: string }
  | { kind: 'bootstrap' }
  | { kind: 'signed_out' }
  | { kind: 'signed_in'; user: SignedInUser };

function phaseFor(state: AuthState): Phase {
  if (state.needs_bootstrap) return { kind: 'bootstrap' };
  if (state.signed_in && state.user) return { kind: 'signed_in', user: state.user };
  return { kind: 'signed_out' };
}

/** REQ-SB-101 -- decides, before anything else renders, whether this
 * person sees the first-Admin screen, the sign-in screen, or the app.
 *
 * Sits INSIDE BootGate, not around it: an install that cannot boot has
 * nothing to sign in to, and asking for a password in front of a broken
 * backend would replace a useful boot error with a login form that
 * cannot work. Boot first, then identity.
 *
 * **A backend that cannot be reached is not "signed out".** Rendering
 * the sign-in screen when `/auth/state` fails would invite someone to
 * type a password into a form whose submit cannot possibly succeed, and
 * would read as "it logged me out" rather than "the server is down" --
 * the same honesty rule the rest of this app keeps about an empty result
 * versus a failed read.
 */
export function AuthGate({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<Phase>({ kind: 'loading' });

  const refresh = useCallback(async () => {
    try {
      setPhase(phaseFor(await fetchAuthState()));
    } catch (error) {
      const detail =
        error instanceof ApiError
          ? `The backend answered ${error.status}.`
          : 'The backend could not be reached.';
      setPhase({ kind: 'unreachable', detail });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const handleSignOut = useCallback(async () => {
    try {
      await signOutRequest();
    } finally {
      // Re-ask rather than assume: the answer decides between the
      // sign-in screen and the first-Admin screen, and only the backend
      // knows which (an Admin who deleted every other account and then
      // signed out is back to an unbootstrapped install).
      await refresh();
    }
  }, [refresh]);

  if (phase.kind === 'loading') {
    return (
      <div className="auth-screen">
        <div className="auth-card auth-card-quiet">Checking who you are…</div>
      </div>
    );
  }

  if (phase.kind === 'unreachable') {
    return (
      <div className="auth-screen">
        <div className="auth-card">
          <h1>Second Brain cannot reach its backend</h1>
          <p className="auth-detail">{phase.detail}</p>
          <p className="auth-note">
            This is not a sign-in problem — there is nothing to sign in to until the
            backend answers. Check that it is running, then try again.
          </p>
          <button type="button" className="auth-primary" onClick={() => void refresh()}>
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (phase.kind === 'bootstrap') {
    return <FirstAdminScreen onBootstrapped={() => void refresh()} />;
  }

  if (phase.kind === 'signed_out') {
    return <SignInScreen onSignedIn={() => void refresh()} />;
  }

  const value: AuthContextValue = {
    user: phase.user,
    signOut: handleSignOut,
    may: (capability: string) => phase.user.capabilities.includes(capability),
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
