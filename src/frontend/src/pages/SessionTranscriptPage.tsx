import { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { refusalText } from '../features/auth/SignInScreen';
import { fetchSessionTranscript } from '../features/hermes-ops/client';
import type { SessionTranscript, TranscriptTurn } from '../features/hermes-ops/client';

const ROLE_LABELS: Record<string, string> = {
  user: 'Asked',
  assistant: 'Agent',
  system: 'System',
  tool: 'Tool',
};

function argumentsOf(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

/** One tool call and the answer it got, as one thing.
 *
 * This pairing is the whole reason the page exists: Hermes records a
 * call and its result as two separate messages joined by an id, so in
 * the raw list they sit far apart and the reader does the join by eye.
 * A call is also the only place a session touches the world — reads the
 * vault, calls an Action, sends mail — so it is given more room than
 * the prose around it rather than less. */
function ToolCall({ call }: { call: TranscriptTurn['tool_calls'][number] }) {
  const [open, setOpen] = useState(false);
  if (call.unreadable) {
    return (
      <div className="transcript-tool transcript-tool-unreadable">
        <strong>A tool call this app could not read.</strong>
        <p className="auth-note">
          Hermes recorded it as text that is not valid JSON. Shown rather than dropped —
          a call nobody can see is exactly what this page exists to surface.
        </p>
        <pre>{call.unreadable}</pre>
      </div>
    );
  }
  return (
    <div className={call.answered ? 'transcript-tool' : 'transcript-tool transcript-tool-dead-end'}>
      <button type="button" className="transcript-tool-head" onClick={() => setOpen((o) => !o)}>
        <span className="transcript-tool-name">{call.name ?? '(unnamed tool)'}</span>
        {call.answered ? (
          <span className="badge badge-success">answered</span>
        ) : (
          <span className="badge badge-warning">no answer</span>
        )}
        <span className="transcript-tool-toggle">{open ? 'Hide' : 'Show'}</span>
      </button>
      {open && (
        <div className="transcript-tool-body">
          <h4>Called with</h4>
          <pre>{argumentsOf(call.arguments) || '(no arguments)'}</pre>
          <h4>Answered</h4>
          {call.answered ? (
            <pre>{call.answer ?? '(empty answer)'}</pre>
          ) : (
            <p className="auth-note">
              Nothing came back for this call. A dead end here is usually where a
              confused ask went wrong.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Turn({ turn }: { turn: TranscriptTurn }) {
  const [showThinking, setShowThinking] = useState(false);
  return (
    <article className={`transcript-turn transcript-turn-${turn.role}`}>
      <header>
        <span className="transcript-role">{ROLE_LABELS[turn.role] ?? turn.role}</span>
        {turn.finish_reason && <span className="auth-note"> · {turn.finish_reason}</span>}
        {turn.tokens !== null && <span className="auth-note"> · {turn.tokens} tokens</span>}
      </header>

      {turn.said && <p className="transcript-said">{turn.said}</p>}

      {turn.thinking && (
        <div className="transcript-thinking">
          <button type="button" onClick={() => setShowThinking((s) => !s)}>
            {showThinking ? 'Hide reasoning' : 'Why it did that'}
          </button>
          {showThinking && <pre>{turn.thinking}</pre>}
        </div>
      )}

      {turn.tool_calls.map((call, index) => (
        <ToolCall key={call.id ?? index} call={call} />
      ))}
    </article>
  );
}

/** REQ-SB-100 — one Hermes session, read rather than dumped.
 *
 * **The route it took is shown before the conversation.** The sequence
 * of tools a session called is the closest thing to a recorded routing
 * decision, and it is what the operator came to see; scrolling a long
 * transcript to reconstruct it by eye is the thing this replaces.
 *
 * **The arithmetic is on the page.** Messages in, turns out, answers
 * folded — so "that is all of it" is checkable rather than trusted.
 * Without it, a folded tool answer is indistinguishable from a message
 * this app quietly failed to render.
 */
export function SessionTranscriptPage() {
  const { sessionId = '' } = useParams();
  const [view, setView] = useState<SessionTranscript | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setView(null);
    setFailure(null);
    fetchSessionTranscript(sessionId)
      .then((answer) => !cancelled && setView(answer))
      .catch((error) => !cancelled && setFailure(refusalText(error)));
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  if (failure) {
    return (
      <>
        <h1>Session transcript</h1>
        <p className="auth-refusal" role="alert">{failure}</p>
      </>
    );
  }
  if (!view) return <><h1>Session transcript</h1><p>Reading the session…</p></>;

  if (!view.reachable) {
    return (
      <>
        <h1>Session transcript</h1>
        <p className="auth-refusal" role="alert" data-testid="transcript-unreachable">
          Hermes could not be reached, so there is no transcript to show. This is not an
          empty session — it is an unread one.
        </p>
        {view.error && <p className="auth-note">{view.error}</p>}
      </>
    );
  }

  const happened = view.what_happened;
  const route = happened.tools_in_order;

  return (
    <>
      <h1>Session transcript</h1>
      <p className="auth-note">{sessionId}</p>

      <section className="transcript-route" data-testid="transcript-route">
        <h2>The route it took</h2>
        {route.length === 0 ? (
          <p className="auth-note">
            This session called no tools at all — it answered from the conversation alone,
            touching nothing.
          </p>
        ) : (
          <>
            <ol className="transcript-route-list">
              {route.map((tool, index) => (
                <li key={`${tool}-${index}`}>{tool}</li>
              ))}
            </ol>
            {happened.tool_calls_without_an_answer > 0 && (
              <p className="auth-refusal" data-testid="transcript-dead-ends">
                {happened.tool_calls_without_an_answer} tool call
                {happened.tool_calls_without_an_answer === 1 ? '' : 's'} got no answer back.
              </p>
            )}
          </>
        )}
        <p className="auth-note">
          {Object.entries(happened.turns_by_role)
            .map(([role, count]) => `${count} ${ROLE_LABELS[role] ?? role}`)
            .join(' · ')}
        </p>
      </section>

      <section>
        <h2>What was said</h2>
        <div className="transcript-turns">
          {view.turns.map((turn, index) => (
            <Turn key={turn.id ?? index} turn={turn} />
          ))}
        </div>
      </section>

      <p className="auth-note" data-testid="transcript-counts">
        {view.counts.messages_in} messages from Hermes, read as {view.counts.turns_out} turns,
        with {view.counts.tool_answers_folded_in} tool answer
        {view.counts.tool_answers_folded_in === 1 ? '' : 's'} folded into the call each
        answered. Nothing else was hidden.
        {view.pagination && view.pagination.returned >= view.pagination.limit && (
          <> This is the first {view.pagination.limit}; the session is longer.</>
        )}
      </p>
    </>
  );
}
