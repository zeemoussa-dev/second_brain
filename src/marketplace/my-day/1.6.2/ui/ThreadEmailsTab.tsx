import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { fetchThreadEmails, type ThreadEmail } from './client';

// My Day's own tab inside the framework's Cockpit (host contract v3,
// `cockpitTabs`). The Cockpit is a generic component for chatting with agents
// about a subject; knowing that a Thread is made of emails, and where they live,
// is this plugin's business -- so the tab and its reader are both here.

interface ThreadEmailsTabProps {
  subjectKind: 'email' | 'meeting';
  subjectNoteStem: string;
}

export function ThreadEmailsTab({ subjectNoteStem }: ThreadEmailsTabProps) {
  const [emails, setEmails] = useState<ThreadEmail[] | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setEmails(null);
    setProblem(null);
    fetchThreadEmails(subjectNoteStem)
      .then((result) => !cancelled && setEmails(result))
      .catch(() => !cancelled && setProblem('Could not read this thread’s emails.'));
    return () => {
      cancelled = true;
    };
  }, [subjectNoteStem]);

  return (
    <>
      <h3>Emails in this thread{emails ? ` (${emails.length})` : ''}</h3>
      {/* "Still loading" is not "there is nothing here" -- the same distinction
          the Cockpit's own panels make. */}
      {problem && <p className="error-text">{problem}</p>}
      {!emails && !problem && <p className="text-muted" role="status">Loading the emails…</p>}
      {emails && emails.length > 0 && (
        <div className="item-list">
          {emails.map((email) => (
            <Link className="item-row" to={`/browse/${encodeURIComponent(email.stem)}`} key={email.stem}>
              <span className="material-symbols-outlined" aria-hidden="true">mail</span>
              <span className="item-row-main">
                <span className="item-row-title">{email.subject}</span>
                <span className="item-row-meta">
                  {email.sender || email.sender_email}
                  {email.received ? ` · ${email.received.slice(0, 16)}` : ''}
                </span>
              </span>
            </Link>
          ))}
        </div>
      )}
      {emails && emails.length === 0 && (
        <div className="empty-state"><p className="text-muted">No captured emails for this thread yet.</p></div>
      )}
    </>
  );
}
