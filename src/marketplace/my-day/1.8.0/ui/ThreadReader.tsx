import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { NoteText } from '../../pluginHost/noteText';
import {
  attachmentUrl,
  fetchThreadDetail,
  fetchThreadEmail,
  type ThreadDetail,
  type ThreadEmailBody,
} from './client';

// One captured Thread, read in place: what it is about, the emails it is made
// of and the files that came with them (operator, 2026-09-25: "the emails tab
// should include the related documents ... as well as the emails it self the
// thread summary. We need to make the email more useful"). Before this the tab
// was an index of subjects -- reading one meant opening the Cockpit, and the
// attachments were only visible there.
//
// The summary and each email body render through the host's `NoteText`, so they
// read exactly as the app renders vault text: markdown, and `[[wikilinks]]` as
// real links into the note view.

function Loading({ label }: { label: string }) {
  return <p className="text-muted" role="status">{label}…</p>;
}

function received(value: string): string {
  // The frontmatter's own string, trimmed to the minute -- reformatting it would
  // invent a timezone the note does not state.
  return value ? value.slice(0, 16) : '';
}

function EmailRow({
  email, threadStem, open, onToggle,
}: {
  email: { stem: string; subject: string; sender: string; sender_email: string; received: string };
  threadStem: string;
  open: boolean;
  onToggle: () => void;
}) {
  const [body, setBody] = useState<ThreadEmailBody | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  // Fetched when the email is opened, not with the thread: a long thread would
  // otherwise carry every body it never shows.
  useEffect(() => {
    if (!open || body || problem) return;
    let cancelled = false;
    fetchThreadEmail(threadStem, email.stem)
      .then((result) => !cancelled && setBody(result))
      .catch(() => !cancelled && setProblem('Could not read this email.'));
    return () => {
      cancelled = true;
    };
  }, [open, body, problem, threadStem, email.stem]);

  return (
    <div className={`my-day-email${open ? ' is-open' : ''}`}>
      <button type="button" className="my-day-email-head" onClick={onToggle} aria-expanded={open}>
        <span className="material-symbols-outlined" aria-hidden="true">{open ? 'expand_more' : 'chevron_right'}</span>
        <span className="my-day-email-head-main">
          <span className="item-row-title">{email.subject}</span>
          <span className="item-row-meta">
            {email.sender || email.sender_email}
            {email.received ? ` · ${received(email.received)}` : ''}
          </span>
        </span>
      </button>
      {open && (
        <div className="my-day-email-body">
          {problem && <p className="error-text">{problem}</p>}
          {!body && !problem && <Loading label="Reading the email" />}
          {body && (
            <>
              {body.sender_email && (
                <p className="text-muted my-day-email-from">From: {body.sender_email}</p>
              )}
              <NoteText text={body.body} />
              <p>
                <Link className="btn-link" to={`/browse/${encodeURIComponent(email.stem)}`}>
                  Open the note →
                </Link>
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export function ThreadReader({ stem }: { stem: string }) {
  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [openEmailStem, setOpenEmailStem] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setProblem(null);
    setOpenEmailStem(null);
    fetchThreadDetail(stem)
      .then((result) => !cancelled && setDetail(result))
      .catch(() => !cancelled && setProblem('Could not read this thread.'));
    return () => {
      cancelled = true;
    };
  }, [stem]);

  if (problem) return <div className="card"><p className="error-text">{problem}</p></div>;
  // "Still loading" is not "there is nothing here" -- the same distinction the
  // Cockpit's own panels make (operator, 2026-09-24: data must not just jump in).
  if (!detail) return <div className="card"><Loading label="Opening the thread" /></div>;

  return (
    <div className="card my-day-thread">
      <div className="my-day-thread-head">
        <h2>{detail.subject}</h2>
        <Link
          className="btn-link"
          to={`/inbox-cockpit/${encodeURIComponent(detail.stem)}`}
          state={{ backTo: '/my-day/emails', backLabel: 'Emails' }}
        >
          Open Cockpit →
        </Link>
      </div>

      <section className="my-day-thread-section">
        <h3>Summary</h3>
        {detail.summary
          ? <NoteText text={detail.summary} />
          : <p className="text-muted">No summary written for this thread yet.</p>}
      </section>

      <section className="my-day-thread-section">
        <h3>Emails ({detail.emails.length})</h3>
        {detail.emails.length > 0 ? (
          <div className="my-day-email-list">
            {detail.emails.map((email) => (
              <EmailRow
                email={email}
                threadStem={detail.stem}
                open={openEmailStem === email.stem}
                onToggle={() => setOpenEmailStem(openEmailStem === email.stem ? null : email.stem)}
                key={email.stem}
              />
            ))}
          </div>
        ) : (
          <p className="text-muted">No captured emails for this thread yet.</p>
        )}
      </section>

      <section className="my-day-thread-section">
        <h3>Attachments ({detail.attachments.length})</h3>
        {detail.attachments.length > 0 ? (
          <div className="item-list">
            {detail.attachments.map((attachment) => (
              attachment.filename ? (
                // The real file, opened by the browser. A note with no file beside
                // it is still worth showing -- it links to the note instead.
                <a
                  className="item-row"
                  href={attachmentUrl(attachment.stem, attachment.filename)}
                  target="_blank"
                  rel="noopener noreferrer"
                  key={attachment.stem}
                >
                  <span className="material-symbols-outlined" aria-hidden="true">attach_file</span>
                  <span className="item-row-main">
                    <span className="item-row-title">{attachment.filename}</span>
                    {/* A captured attachment's note is titled after the file it
                        holds, so repeating it under the name says nothing; an
                        upload with its own caption still shows it. */}
                    {attachment.title && !attachment.title.includes(attachment.filename) && (
                      <span className="item-row-meta">{attachment.title}</span>
                    )}
                  </span>
                </a>
              ) : (
                <Link className="item-row" to={`/browse/${encodeURIComponent(attachment.stem)}`} key={attachment.stem}>
                  <span className="material-symbols-outlined" aria-hidden="true">description</span>
                  <span className="item-row-main">
                    <span className="item-row-title">{attachment.title || attachment.stem}</span>
                    <span className="item-row-meta">No file stored with this note</span>
                  </span>
                </Link>
              )
            ))}
          </div>
        ) : (
          <p className="text-muted">Nothing was attached to this thread.</p>
        )}
      </section>
    </div>
  );
}
