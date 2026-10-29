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

/** A few words off a turn, for the jump list. Long enough to recognise
 *  which turn it is, short enough not to become a second transcript
 *  down the side. A turn with no words is named by what it did
 *  instead, because "(no text)" repeated twenty times is not a
 *  navigation aid. */
/** Past this many calls the route stops being a sequence you read and
 *  becomes a wall you scroll. Twelve fits on a screen beside the rail;
 *  a cron session's fifty-odd does not. */
const ROUTE_IS_LONG = 12;

/** Each tool and how often it was called, commonest first — the same
 *  information as the full list, in one line. */
function countBy(tools: string[]): Array<[string, number]> {
  const counts = new Map<string, number>();
  for (const tool of tools) counts.set(tool, (counts.get(tool) ?? 0) + 1);
  return [...counts.entries()].sort((left, right) => right[1] - left[1]);
}

/** Text that can be long, shown short until asked.
 *
 * A cron session's "ask" is not a sentence a person typed -- it is a
 * machine preamble with the whole SKILL.md inlined, running to
 * thousands of characters (operator, 2026-10-24: "what's asked is not
 * readable"). Clamped, the first lines are the instruction and the
 * rest is one click away.
 *
 * Deliberately NOT clever about WHICH part to show. Guessing where
 * the "real" ask ends inside a generated prompt would be wrong
 * sometimes and there would be no way to tell when -- so it shows the
 * beginning, says how much more there is, and lets the reader decide.
 */
function Clamped({ text, lines = 6 }: { text: string; lines?: number }) {
  const [open, setOpen] = useState(false);
  const allLines = text.split('\n');
  const isLong = allLines.length > lines || text.length > 420;
  if (!isLong) return <span className="transcript-said">{text}</span>;
  const shown = open ? text : allLines.slice(0, lines).join('\n').slice(0, 420);
  return (
    <span className="transcript-said">
      {shown}
      {!open && '…'}
      {' '}
      <button type="button" className="auth-link-button" onClick={() => setOpen((o) => !o)}>
        {open
          ? 'show less'
          : `show all (${allLines.length} lines, ${text.length.toLocaleString()} characters)`}
      </button>
    </span>
  );
}

function snippetOf(turn: TranscriptTurn): string {
  const said = (turn.said ?? '').trim().replace(/\s+/g, ' ');
  if (said) return said.length > 48 ? `${said.slice(0, 48)}…` : said;
  const tools = turn.tool_calls.map((call) => call.name).filter(Boolean);
  return tools.length > 0 ? tools.join(', ') : '(nothing said)';
}

function Turn({ turn, anchor }: { turn: TranscriptTurn; anchor?: string }) {
  const [showThinking, setShowThinking] = useState(false);
  return (
    <article id={anchor} className={`transcript-turn transcript-turn-${turn.role}`}>
      <header>
        <span className="transcript-role">{ROLE_LABELS[turn.role] ?? turn.role}</span>
        {turn.finish_reason && <span className="auth-note"> · {turn.finish_reason}</span>}
        {turn.tokens !== null && <span className="auth-note"> · {turn.tokens} tokens</span>}
      </header>

      {turn.said && <p><Clamped text={turn.said} /></p>}

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
  const [show, setShow] = useState<'conversation' | 'everything' | 'tools'>('conversation');
  const [routeOpen, setRouteOpen] = useState(false);

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

  // Who actually asked for something. `user` is the person; everything
  // else in a session is the machine answering itself.
  const asks = view.turns
    .map((turn, position) => ({ turn, position }))
    .filter(({ turn }) => turn.role === 'user' && (turn.said ?? '').trim() !== '');

  const shownTurns = view.turns.filter((turn) => {
    if (show === 'everything') return true;
    const hasWords = (turn.said ?? '').trim() !== '';
    // "What was said" keeps anything with words in it, from either
    // side — dropping an assistant turn that answered in prose would
    // hide the reply to the very ask this view exists to show.
    if (show === 'conversation') return hasWords;
    return turn.tool_calls.length > 0;
  });

  return (
    <>
      <h1>Session transcript</h1>
      <p className="auth-note">{sessionId}</p>

      {/* The notes view's own rail, reused rather than reinvented
          (operator, 2026-10-24: "add the same right navigation we have
          on the notes so I can jump sections, as I need to scroll a
          lot when the ask is coming from a cron job"). A cron session
          here runs to dozens of turns, and the asks are a handful of
          them. Same classes as the note rail, so it sticks, scrolls
          and collapses under the content on a narrow pane exactly as
          that one does. */}
      <div className="note-detail-layout">
        <div className="note-detail-main">

      <section id="transcript-route" className="transcript-route" data-testid="transcript-route">
        <h2>The route it took</h2>
        {route.length === 0 ? (
          <p className="auth-note">
            This session called no tools at all — it answered from the conversation alone,
            touching nothing.
          </p>
        ) : (
          <>
            {/* A cron session's route runs to fifty-odd calls, mostly
                the same few tools over and over, and printed in full
                it is a page of scrolling before the conversation even
                starts (operator, 2026-10-24: "I want to collapse
                stuff"). Collapsed, it says the same thing in one line
                — which tools, how many times — and opens in full when
                the order actually matters. */}
            {route.length > ROUTE_IS_LONG && !routeOpen ? (
              <p data-testid="transcript-route-summary">
                <strong>{route.length} calls</strong>:{' '}
                {countBy(route).map(([tool, count], index) => (
                  <span key={tool}>
                    {index > 0 && ', '}
                    <code>{tool}</code> &times;{count}
                  </span>
                ))}{' '}
                <button type="button" className="auth-link-button" onClick={() => setRouteOpen(true)}>
                  show the order
                </button>
              </p>
            ) : (
              <>
                <ol className="transcript-route-list">
                  {route.map((tool, index) => (
                    <li key={`${tool}-${index}`}>{tool}</li>
                  ))}
                </ol>
                {route.length > ROUTE_IS_LONG && (
                  <button type="button" className="auth-link-button" onClick={() => setRouteOpen(false)}>
                    collapse the route
                  </button>
                )}
              </>
            )}
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

      {/* The asks, lifted out of the noise (operator, 2026-10-24:
          "what's asked is not readable, some better representation is
          needed").

          Measured on a real session before building this: 32 turns, 26
          of them assistant, most with NO text and a single tool call —
          so the handful of turns where a person actually said
          something were buried among two dozen that only machines
          care about. They are the first thing on the page now, in
          order, and the full exchange is still below. */}
      {asks.length > 0 && (
        <section id="transcript-asks" data-testid="transcript-asks">
          <h2>What was asked ({asks.length})</h2>
          <ol className="transcript-asks">
            {asks.map(({ turn, position }) => (
              <li id={`ask-${position}`} key={turn.id ?? position}>
                <Clamped text={turn.said ?? ''} />
              </li>
            ))}
          </ol>
        </section>
      )}

      <section id="transcript-said">
        <h2>What was said</h2>
        <div className="transcript-controls">
          {/* Three readings of one transcript. `conversation` is the
              default because it is what the page is for: 26 of 32
              turns on a real session are tool traffic, and showing
              them by default is what made this unreadable. */}
          {(['conversation', 'everything', 'tools'] as const).map((mode) => (
            <label key={mode}>
              <input
                type="radio"
                name="transcript-view"
                checked={show === mode}
                onChange={() => setShow(mode)}
                data-testid={`transcript-show-${mode}`}
              />{' '}
              {mode === 'conversation'
                ? 'What was said'
                : mode === 'tools' ? 'Only what it did' : 'Everything'}
            </label>
          ))}
          <span className="auth-note">
            showing {shownTurns.length} of {view.turns.length} turns
          </span>
        </div>
        <div className="transcript-turns">
          {shownTurns.length === 0 ? (
            <p className="auth-note" data-testid="transcript-nothing-shown">
              Nothing in this session matches that view — try “Everything”.
            </p>
          ) : (
            shownTurns.map((turn, index) => (
              <Turn
                key={turn.id ?? index}
                turn={turn}
                anchor={`turn-${view.turns.indexOf(turn)}`}
              />
            ))
          )}
        </div>
      </section>

        </div>

        <aside className="note-rail" aria-label="Jump to a part of this session">
          <section className="note-rail-section">
            <h3 className="note-rail-title">On this page</h3>
            <ul className="note-detail-toc-list">
              <li><a href="#transcript-route" data-level="2">The route it took</a></li>
              {asks.length > 0 && (
                <li><a href="#transcript-asks" data-level="2">What was asked ({asks.length})</a></li>
              )}
              {asks.map(({ turn, position }, index) => (
                <li key={`nav-ask-${position}`}>
                  <a href={`#ask-${position}`} data-level="3">
                    {index + 1}. {snippetOf(turn)}
                  </a>
                </li>
              ))}
              <li><a href="#transcript-said" data-level="2">What was said ({shownTurns.length})</a></li>
              {/* One entry per turn currently SHOWN, so the rail and
                  the page always agree -- a jump target for a turn the
                  chosen view has hidden would scroll to nothing. */}
              {shownTurns.map((turn) => (
                <li key={`nav-turn-${view.turns.indexOf(turn)}`}>
                  <a href={`#turn-${view.turns.indexOf(turn)}`} data-level="3">
                    {ROLE_LABELS[turn.role] ?? turn.role}: {snippetOf(turn)}
                  </a>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>

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
