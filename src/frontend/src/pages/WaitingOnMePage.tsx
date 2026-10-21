import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router';
import { refusalText } from '../features/auth/SignInScreen';
import {
  answerHumanStep,
  fetchQuestionsWaitingOnAPerson,
  type HumanDecision,
  type WaitingQuestion,
} from '../features/settings/workflowsApiClient';

/** REQ-SB-103 — the questions this install is waiting on a person to
 * answer.
 *
 * **This exists because a human step can hold a run forever.** When a
 * Workflow stops to ask, the run sits at `awaiting_person` until
 * somebody answers, and a run that waits indefinitely with nothing
 * showing it is waiting is worse than one that fails: nothing is broken,
 * nothing is logged, and nothing happens.
 *
 * **A question through a door nobody owns appears on everybody's list**,
 * marked as such. Leaving it off each person's list is exactly how it
 * would be waited on by no one — and attributing it to whoever happened
 * to ask would be inventing a decision-maker.
 *
 * **Asked over WhatsApp, answerable here.** The agent in the
 * conversation can record the answer from there; this page is the same
 * decision made in the app, and either way the record says who made it
 * and what they actually said.
 */
function asksAsText(asks: unknown): string {
  if (typeof asks === 'string') return asks;
  if (asks === null || asks === undefined) return '(the question is empty)';
  return JSON.stringify(asks, null, 2);
}

export function WaitingOnMePage() {
  const [scope, setScope] = useState<'mine' | 'all'>('mine');
  const [questions, setQuestions] = useState<WaitingQuestion[] | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [said, setSaid] = useState<Record<string, string>>({});
  const [edit, setEdit] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [refused, setRefused] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    try {
      setQuestions(await fetchQuestionsWaitingOnAPerson(scope));
      setFailure(null);
    } catch (error) {
      setFailure(refusalText(error));
    }
  }, [scope]);

  useEffect(() => {
    void load();
  }, [load]);

  async function answer(question: WaitingQuestion, decision: HumanDecision) {
    const key = question.run_id;
    setBusy(key);
    setRefused((previous) => ({ ...previous, [key]: '' }));
    try {
      await answerHumanStep(question.run_id, question.step_id ?? '', {
        decision,
        said: said[key] ?? '',
        // Only an edit replaces what was proposed. Sending the box's
        // contents on an approval would turn a stray keystroke into a
        // silent rewrite of what goes out.
        result: decision === 'edited' ? (edit[key] ?? '') : undefined,
      });
      await load();
    } catch (error) {
      setRefused((previous) => ({ ...previous, [key]: refusalText(error) }));
    } finally {
      setBusy(null);
    }
  }

  if (failure && !questions) {
    return <><h1>Waiting on you</h1><p className="auth-refusal" role="alert">{failure}</p></>;
  }
  if (!questions) return <><h1>Waiting on you</h1><p>Reading the open questions…</p></>;

  return (
    <>
      <h1>Waiting on you</h1>
      <p className="text-muted">
        Workflows that stopped to ask. Each one is holding — nothing after the question has run,
        and it will wait until somebody answers.
      </p>

      <p className="auth-note">
        <label>
          <input
            type="radio"
            name="waiting-scope"
            checked={scope === 'mine'}
            onChange={() => setScope('mine')}
          />{' '}
          Mine
        </label>{' '}
        <label>
          <input
            type="radio"
            name="waiting-scope"
            checked={scope === 'all'}
            onChange={() => setScope('all')}
          />{' '}
          Everyone's
        </label>
        {' — '}“Mine” is every question that came in through a door declared as yours, plus every
        question through a door nobody owns.
      </p>

      {failure && <p className="auth-refusal" role="alert">{failure}</p>}

      {questions.length === 0 ? (
        <p className="auth-note" data-testid="waiting-empty">
          Nothing is waiting on you. A Workflow only lands here when one of its steps is a
          question for a person.
        </p>
      ) : (
        <div className="item-list" data-testid="waiting-list">
          {questions.map((question) => (
            <div className="item-row" key={question.run_id} data-testid={`waiting-${question.run_id}`}>
              {question.unreadable ? (
                <div className="item-row-main">
                  <span className="item-row-title">Run {question.run_id}</span>
                  <span className="auth-refusal" role="alert">
                    This run is waiting on somebody and its record could not be read, so what it
                    is asking is unknown: {question.unreadable}
                  </span>
                </div>
              ) : (
                <>
                  <div className="item-row-main">
                    <span className="item-row-title">
                      {question.request_kind || question.workflow_id}
                    </span>
                    <pre className="item-row-meta" style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                      {asksAsText(question.asks)}
                    </pre>
                    <span className="item-row-meta">
                      {question.workflow_id} · step {question.step_id}
                      {question.description ? ` · ${question.description}` : ''}
                      {question.asked_at ? ` · asked ${question.asked_at}` : ''}
                    </span>
                    <span className="item-row-meta">
                      {question.is_for_anybody
                        ? 'Came in through a door nobody owns, so it is waiting on anybody.'
                        : `For ${question.for_person?.display_name
                            || question.for_person?.username}.`}
                      {question.entry_point?.source
                        ? ` Asked over ${question.entry_point.source}.`
                        : ''}
                      {' '}
                      <Link to="/entry-points">Declare whose door this is</Link>
                    </span>
                    <input
                      className="input"
                      placeholder="what you want to say back (recorded as your words)"
                      aria-label={`Your answer to ${question.step_id}`}
                      value={said[question.run_id] ?? ''}
                      onChange={(event) =>
                        setSaid((d) => ({ ...d, [question.run_id]: event.target.value }))
                      }
                    />
                    {question.allows_edit && (
                      <textarea
                        className="input"
                        rows={3}
                        style={{ width: '100%', resize: 'vertical' }}
                        placeholder="change what goes on from here — this replaces what was proposed"
                        aria-label={`What should go on from ${question.step_id}`}
                        value={edit[question.run_id] ?? ''}
                        onChange={(event) =>
                          setEdit((d) => ({ ...d, [question.run_id]: event.target.value }))
                        }
                      />
                    )}
                    {refused[question.run_id] && (
                      <span className="auth-refusal" role="alert">{refused[question.run_id]}</span>
                    )}
                  </div>
                  <div className="item-row-actions">
                    <button
                      type="button"
                      className="btn"
                      disabled={busy === question.run_id}
                      onClick={() => void answer(question, 'approved')}
                    >
                      Approve
                    </button>
                    {/* Offered only where the Workflow says the person
                        may change it. The run refuses an edit otherwise,
                        and a button that always refused would be a
                        promise this page cannot keep. */}
                    {question.allows_edit && (
                      <button
                        type="button"
                        className="btn"
                        disabled={busy === question.run_id || !(edit[question.run_id] ?? '').trim()}
                        onClick={() => void answer(question, 'edited')}
                      >
                        Send my version
                      </button>
                    )}
                    <button
                      type="button"
                      className="btn btn-danger"
                      disabled={busy === question.run_id}
                      onClick={() => void answer(question, 'declined')}
                    >
                      Decline
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
