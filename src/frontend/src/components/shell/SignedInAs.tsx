import { NavLink } from 'react-router';
import { useAuth } from '../../features/auth/AuthGate';
import { ROLE_LABELS } from '../../features/auth/authApiClient';

/** The initials shown in the avatar. Taken from the display name when
 * there is one and the username otherwise, so an account with no display
 * name still gets something meaningful rather than a blank disc.
 *
 * Two initials at most: "Robin Fictional" is RF, "robin" is R. A longer
 * run of letters stops being readable at avatar size, which is the only
 * size this is ever rendered at. */
export function initialsFor(displayName: string, username: string): string {
  const source = (displayName || username).trim();
  if (!source) return '?';
  const words = source.split(/\s+/).filter(Boolean);
  const letters = words.length > 1 ? words[0][0] + words[words.length - 1][0] : source[0];
  return letters.toUpperCase();
}

/** REQ-SB-101 -- who you are signed in as, at the foot of the sidebar
 * beside the version (operator, 2026-10-21).
 *
 * **Shows the role, not just the name.** On an install several people
 * share, "why can't I see that button" is almost always "you are signed
 * in as a User", and a name alone does not answer it. The role is the
 * cheapest possible place to put that answer, and it sits where someone
 * looking for why a screen is missing will actually look.
 *
 * Hidden entirely when the sidebar is collapsed rather than shrunk to a
 * lone avatar: a disc with two letters and no name is a puzzle, and the
 * sign-out button underneath it would be a one-click action nobody could
 * identify.
 */
export function SignedInAs({ collapsed }: { collapsed: boolean }) {
  const { user, signOut } = useAuth();
  if (collapsed) return null;

  return (
    <div className="signed-in-as" data-testid="signed-in-as">
      {/* The avatar and name are the link to your own profile -- the
          place people already look for it, and it keeps the sidebar
          foot to two controls rather than three. */}
      <NavLink to="/profile" className="signed-in-as-link" title="Your profile">
        <span className="signed-in-as-avatar" aria-hidden="true">
          {initialsFor(user.display_name, user.username)}
        </span>
        <span className="signed-in-as-who">
          <span className="signed-in-as-name">{user.display_name || user.username}</span>
          <span className="signed-in-as-role">{ROLE_LABELS[user.role]}</span>
        </span>
      </NavLink>
      <button
        type="button"
        className="signed-in-as-sign-out"
        data-testid="sign-out"
        title={`Sign out of ${user.username}`}
        onClick={() => void signOut()}
      >
        Sign out
      </button>
    </div>
  );
}
