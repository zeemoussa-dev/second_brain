import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { Field } from '../features/settings/Field';
import {
  describeOperatorProfileRefusal,
  fetchOperatorProfile,
  saveOperatorProfile,
  type OperatorProfile,
  type OperatorTeamMember,
} from '../features/settings/operatorProfileApiClient';

// The Operator Profile editor (REQ-SB-95-US-01-T05, ADR-032/ADR-038) -- the
// one place this install records who its agents act for, on the already
// approved .item-list/.item-row and .input/Save changes families the System
// and Workflows pages established. No new visual system; the only new
// interaction is the repeating email+role team row.
//
// What this screen is on the right side of:
//
// - **The operator's own address is NOT editable here, and is not drawn as
//   though it were.** It is the `SELF_EMAIL` setting, owned by Settings >
//   System (`ADR-038`), and the Profile only MIRRORS it. It is rendered as
//   text with the surface that owns it named beside it -- never as a
//   disabled input, which reads as "editable, just not now", and never as a
//   live input that would silently fail. The write body has no field for it
//   by type, so this page cannot normally provoke the backend's `409`; if
//   one arrives anyway it is rendered with the backend's own sentence,
//   because that sentence names where the address really lives.
// - **"Not saved yet" and "could not be read" are different renderings, and
//   neither is an empty form.** An install that has never saved reads back
//   as `is_configured: false` and gets a form that SAYS it is blank because
//   nothing is stored. A failed `GET` gets no form at all: an empty editor
//   after a failed read would claim to show a saved, blank Profile. That is
//   `SPRINT-091`'s rule -- `.empty-state` means "we read it and it was
//   empty", and a failed read may never borrow that look.
// - **A save re-renders from the PUT's own response, never from the draft.**
//   The backend drops a team entry with no email (the email IS the join key
//   onto the Person note), so the stored record can legitimately differ from
//   what was submitted. Showing the submitted draft back would report rows
//   as saved that are not on disk.
//
// Person notes are NOT edited here and a colleague has no name field: the
// Profile records membership, the vault describes the person (`ADR-032`).

interface ProfileDraft {
  name: string;
  otherEmailAddresses: string[];
  timezone: string;
  team: OperatorTeamMember[];
}

function toDraft(profile: OperatorProfile): ProfileDraft {
  return {
    name: profile.name,
    otherEmailAddresses: [...profile.other_email_addresses],
    timezone: profile.timezone,
    team: profile.team.map((member) => ({ ...member })),
  };
}

export function SettingsOperatorPage() {
  const [profile, setProfile] = useState<OperatorProfile | null>(null);
  const [readError, setReadError] = useState<string | null>(null);
  const [draft, setDraft] = useState<ProfileDraft | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function reload() {
    return fetchOperatorProfile().then(
      (stored) => {
        setProfile(stored);
        setDraft(toDraft(stored));
        setReadError(null);
      },
      (error) => {
        // Both are cleared deliberately: with no readable record there is
        // nothing honest to put in an editor, so none is rendered.
        setProfile(null);
        setDraft(null);
        setReadError(describeOperatorProfileRefusal(error));
      },
    );
  }

  useEffect(() => {
    reload();
  }, []);

  function patchDraft(patch: Partial<ProfileDraft>) {
    setDraft((previous) => (previous === null ? previous : { ...previous, ...patch }));
  }

  function patchTeamMember(index: number, patch: Partial<OperatorTeamMember>) {
    setDraft((previous) => (previous === null ? previous : {
      ...previous,
      team: previous.team.map((member, position) => (position === index ? { ...member, ...patch } : member)),
    }));
  }

  // Every list edit below reads the PREVIOUS draft rather than the one this
  // render closed over: two rows changed before React re-renders would
  // otherwise both start from the same stale list, and the second would
  // silently undo the first.
  function patchOtherAddress(index: number, address: string) {
    setDraft((previous) => (previous === null ? previous : {
      ...previous,
      otherEmailAddresses: previous.otherEmailAddresses.map(
        (existing, position) => (position === index ? address : existing),
      ),
    }));
  }

  function removeOtherAddress(index: number) {
    setDraft((previous) => (previous === null ? previous : {
      ...previous,
      otherEmailAddresses: previous.otherEmailAddresses.filter((_, position) => position !== index),
    }));
  }

  function addOtherAddress() {
    setDraft((previous) => (previous === null ? previous : {
      ...previous,
      otherEmailAddresses: [...previous.otherEmailAddresses, ''],
    }));
  }

  function removeTeamMember(index: number) {
    setDraft((previous) => (previous === null ? previous : {
      ...previous,
      team: previous.team.filter((_, position) => position !== index),
    }));
  }

  function addTeamMember() {
    setDraft((previous) => (previous === null ? previous : {
      ...previous,
      team: [...previous.team, { email: '', role: '' }],
    }));
  }

  async function handleSave() {
    if (draft === null) return;
    setSaving(true);
    setSaveError(null);
    setSaveMessage(null);
    const submittedTeamRows = draft.team.length;
    try {
      const stored = await saveOperatorProfile({
        name: draft.name,
        other_email_addresses: draft.otherEmailAddresses,
        timezone: draft.timezone,
        team: draft.team,
      });
      setProfile(stored);
      setDraft(toDraft(stored));
      const droppedTeamRows = submittedTeamRows - stored.team.length;
      setSaveMessage(
        droppedTeamRows > 0
          ? `Saved. ${droppedTeamRows} team row(s) had no email address and were not stored — the email is what reaches a colleague's Person note.`
          : 'Saved. The fields below are the stored record, as the save returned it.',
      );
    } catch (error) {
      // Nothing was written -- every refusal happens before the record is
      // replaced -- so the draft is kept exactly as authored and the
      // backend's own sentence is what the operator reads.
      setSaveError(describeOperatorProfileRefusal(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Operator Profile</h1>
      <p className="text-muted">
        Who this install's agents act for: your name, your other mail addresses, your timezone, and
        your team as a list of email addresses each with a role. One record, edited here and nowhere
        else. A colleague is recorded as membership only — their email and their role — because your
        vault's Person notes are where a person is actually described.
      </p>

      {readError !== null && (
        <div className="card" data-testid="operator-read-error">
          <h2>Could not be read</h2>
          <p className="text-muted">
            <span className="badge badge-danger">Could not be read</span>{' '}
            This install's Operator Profile could not be read from <code>GET /operator/profile</code>:{' '}
            {readError}
          </p>
          <p className="text-muted">
            No editor is shown, on purpose: an empty form here would look like a saved Profile with
            nothing in it. Nothing has been written, and nothing can be saved until the record can be
            read back.
          </p>
          <button type="button" className="btn" data-testid="operator-read-retry" onClick={reload}>
            Try again
          </button>
        </div>
      )}

      {profile === null && readError === null && <p className="text-muted">Loading...</p>}

      {profile !== null && draft !== null && (
        <>
          {/* The mirror, in its own card above the editor so it cannot be
              mistaken for one of the fields below it (`ADR-038`). */}
          <div className="card" data-testid="operator-own-address-card">
            <h2>Your own email address</h2>
            <div className="item-list">
              <div className="item-row">
                <span className="material-symbols-outlined settings-card-icon" aria-hidden="true">
                  alternate_email
                </span>
                <div className="item-row-main" style={{ flex: 1 }}>
                  <span className="item-row-title" data-testid="operator-own-address">
                    {profile.own_address.email === ''
                      ? 'Not set on this install yet'
                      : profile.own_address.email}
                  </span>
                  <span className="item-row-meta" data-testid="operator-own-address-pointer">
                    <span className="badge">Read-only here</span>{' '}
                    The Operator Profile does not store this address — it shows the{' '}
                    <code>{profile.own_address.setting_key}</code> setting, which is edited on{' '}
                    <Link to="/settings/system">{profile.own_address.edited_at}</Link>. Change it
                    there and this line follows.
                  </span>
                </div>
                <div className="item-row-actions">
                  <Link className="btn" to="/settings/system" data-testid="operator-own-address-editor-link">
                    Edit on Settings &rsaquo; System
                  </Link>
                </div>
              </div>
            </div>
          </div>

          <div className="card" style={{ marginTop: 'var(--space-4)' }} data-testid="operator-editor">
            <h2>Profile</h2>

            {profile.is_configured ? (
              <p className="text-muted" data-testid="operator-configured">
                <span className="badge badge-success">Saved</span>{' '}
                Read from this install's stored Operator Profile.
              </p>
            ) : (
              <p className="text-muted" data-testid="operator-not-configured">
                <span className="badge">Not saved yet</span>{' '}
                No Operator Profile has been saved on this install yet — the read succeeded and
                reported <code>is_configured: false</code>. The fields below are empty because there
                is nothing stored, not because a saved Profile is blank. (A stored Profile the
                backend could not parse is reported the same way; it does not report a saved record
                it cannot read.)
              </p>
            )}

            {saveError !== null && (
              <p className="text-muted" data-testid="operator-save-error">
                <span className="badge badge-danger">Save refused</span> {saveError}
              </p>
            )}
            {saveMessage !== null && (
              <p className="text-muted" data-testid="operator-save-message">{saveMessage}</p>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <Field label="Your name">
                <input
                  className="input"
                  data-testid="operator-name"
                  placeholder="the name your agents should use for you"
                  value={draft.name}
                  onChange={(event) => patchDraft({ name: event.target.value })}
                />
              </Field>

              <Field label="Your timezone">
                <input
                  className="input"
                  data-testid="operator-timezone"
                  placeholder="e.g. Europe/Amsterdam"
                  value={draft.timezone}
                  onChange={(event) => patchDraft({ timezone: event.target.value })}
                />
              </Field>

              <Field label="Your other mail addresses">
                <span className="item-row-meta">
                  Addresses that are also yours. Your own address above is not one of these — it is
                  the <code>{profile.own_address.setting_key}</code> setting and is never stored here.
                </span>
                <div className="item-list" data-testid="operator-other-addresses">
                  {draft.otherEmailAddresses.map((address, index) => (
                    <div className="item-row" key={`other-address-${index}`} data-testid={`operator-other-address-row-${index}`}>
                      <div className="item-row-main">
                        <input
                          className="input"
                          data-testid={`operator-other-address-${index}`}
                          placeholder="another.address@example.test"
                          value={address}
                          onChange={(event) => patchOtherAddress(index, event.target.value)}
                        />
                        {address.trim() === '' && (
                          <span className="item-row-meta" data-testid={`operator-other-address-blank-${index}`}>
                            Empty — this row is not stored.
                          </span>
                        )}
                      </div>
                      <div className="item-row-actions">
                        <button
                          type="button"
                          className="btn btn-danger"
                          data-testid={`operator-other-address-remove-${index}`}
                          onClick={() => removeOtherAddress(index)}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                  {draft.otherEmailAddresses.length === 0 && (
                    <span className="item-row-meta" data-testid="operator-other-addresses-none">
                      No other addresses recorded.
                    </span>
                  )}
                  <div>
                    <button
                      type="button"
                      className="btn"
                      data-testid="operator-other-address-add"
                      onClick={addOtherAddress}
                    >
                      Add address
                    </button>
                  </div>
                </div>
              </Field>

              <Field label="Your team">
                <span className="item-row-meta">
                  One row per colleague: their email address and their role. Nothing else about them
                  is recorded here — the email is what reaches their Person note in your vault, and
                  that note is where they are described.
                </span>
                <div className="item-list" data-testid="operator-team">
                  {draft.team.map((member, index) => (
                    <div className="item-row" key={`team-member-${index}`} data-testid={`operator-team-row-${index}`}>
                      <div className="item-row-main">
                        <input
                          className="input"
                          data-testid={`operator-team-email-${index}`}
                          placeholder="colleague@example.test"
                          value={member.email}
                          onChange={(event) => patchTeamMember(index, { email: event.target.value })}
                        />
                        <input
                          className="input"
                          data-testid={`operator-team-role-${index}`}
                          placeholder="their role, e.g. Delivery Lead"
                          value={member.role}
                          onChange={(event) => patchTeamMember(index, { role: event.target.value })}
                        />
                        {member.email.trim() === '' && (
                          <span className="item-row-meta" data-testid={`operator-team-blank-${index}`}>
                            No email address — this row is not stored. The email is the only thing
                            that can reach a real person.
                          </span>
                        )}
                      </div>
                      <div className="item-row-actions">
                        <button
                          type="button"
                          className="btn btn-danger"
                          data-testid={`operator-team-remove-${index}`}
                          onClick={() => removeTeamMember(index)}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                  {draft.team.length === 0 && (
                    <span className="item-row-meta" data-testid="operator-team-none">
                      No colleagues recorded.
                    </span>
                  )}
                  <div>
                    <button
                      type="button"
                      className="btn"
                      data-testid="operator-team-add"
                      onClick={addTeamMember}
                    >
                      Add colleague
                    </button>
                  </div>
                </div>
              </Field>

              <div className="item-row-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  data-testid="operator-save"
                  disabled={saving}
                  onClick={handleSave}
                >
                  {saving ? 'Saving…' : 'Save changes'}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
