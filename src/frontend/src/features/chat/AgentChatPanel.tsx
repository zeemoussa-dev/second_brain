import { useEffect, useRef, useState } from 'react';
import {
  answerChatApproval,
  resetChatSession,
  sendChatMessageWithAttachment,
  streamChatMessage,
  type ChatStreamEvent,
} from '../agents-map/agentsApiClient';
import { ChatMessageText } from '../../components/ChatMessageText';

// Extracted (2026-08-24, operator: "Create a new Tab we call Chat where
// we can Chat with this Agent since it talks to everything") from
// AgentDetailPanel.tsx's own inline Chat tab -- that panel still uses
// this exact component for its own Chat tab (byte-identical behavior,
// just no longer a copy), and the new standalone ChatPage.tsx uses it
// directly against Primary. Self-contained: owns its own message
// thread/draft/attachment state, so either call site just needs an
// agentId + a place to render it.
interface ChatMessage {
  role: 'user' | 'agent';
  text: string;
  isError?: boolean;
  // Real thinking/status lines collected while this reply was streaming
  // in (2026-08-24, operator: "stream the output... at least I will
  // feel Agents are doing something") -- rendered collapsed, separate
  // from `text` (the actual reply), never merged into it.
  activity?: string[];
  // True only while this bubble's own `text` is still being appended to
  // live -- false (or omitted) once its `complete`/`error` frame lands.
  isStreaming?: boolean;
  // Set when the agent is BLOCKED waiting to be allowed to do this.
  // The turn is still open on Hermes' side, so this bubble carries the
  // decision rather than being a dead end the operator can only type
  // at (operator, 2026-10-24: "when I reply Always Approve something
  // crash" -- a typed reply went in as a new prompt while Hermes sat
  // waiting for `approval.respond`).
  awaitingApproval?: boolean;
  // REQ-SB-82-US-06-T08 -- client-only, in-memory identity for the
  // reply-to affordance below; assigned at append time, never persisted
  // and never sent to the backend as-is (ADR-012 point 5: this surface
  // has zero message-id/persistence concept otherwise).
  localId: string;
}

const ACCEPTED_EXTENSIONS = ['.pdf', '.txt', '.md'];
// ~5 lines at this input's own real font-size/line-height/padding
// (chat-message-input, agent-panel.css) -- the real ceiling
// handleDraftChange auto-grows up to before it starts scrolling
// internally instead of growing further.
const _CHAT_INPUT_MAX_HEIGHT_PX = 132;
// Same "truncated quote" convention as Cockpit's own reply-to preview
// (REQ-SB-82-US-06-T07) -- long enough to recognize the message, short
// enough that the strip doesn't dwarf the composer beneath it.
const _REPLY_PREVIEW_MAX_CHARS = 140;

function truncateForReplyPreview(text: string): string {
  const trimmed = text.trim();
  return trimmed.length > _REPLY_PREVIEW_MAX_CHARS
    ? `${trimmed.slice(0, _REPLY_PREVIEW_MAX_CHARS)}…`
    : trimmed;
}

interface AgentChatPanelProps {
  agentId: string;
  agentName: string;
  // AgentDetailPanel's own History tab needs to know a new turn just
  // landed so it can refresh; ChatPage has no History tab and omits
  // this entirely rather than being handed a no-op callback.
  onMessageSent?: () => void;
  /** Which stored conversation this panel is showing. Changing it starts the
   *  thread again from `initialMessages`, exactly as changing `agentId` does.
   *  The side panel passes neither and keeps its in-memory-only behaviour. */
  conversationId?: string;
  initialMessages?: ChatMessage[];
  /** Every change to the thread, for a caller that persists it. Called with
   *  the whole list because that is what gets saved -- see `saveMessages`. */
  onThreadChanged?: (messages: ChatMessage[]) => void;
}

/** How long the turn in flight has been running.
 *
 * A relay to a specialist is a single blocked tool call: Hermes emits
 * one `tool.start` and then nothing until it finishes. Measured on a
 * real ADNOC relay that was 10s of Primary deciding plus 215s of the
 * specialist working -- three and a half minutes during which the one
 * activity line on screen never changed. It was accurate and it was
 * indistinguishable from a hang.
 *
 * **It also says when a turn is near the ceiling.** The whole turn is
 * cut off at `_CHAT_TURN_TIMEOUT_S` (360s, agent_chat_stream.py), and
 * the real relay above used 63% of it. Reaching that limit loses the
 * answer entirely, so the warning comes before the loss, not after.
 */
const TURN_CUTOFF_SECONDS = 360;
const TURN_IS_SLOW_SECONDS = 180;

function Elapsed({ since }: { since: number | null }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (since === null) return;
    const tick = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(tick);
  }, [since]);
  if (since === null) return null;

  const seconds = Math.max(0, Math.floor((now - since) / 1000));
  const shown = seconds < 60
    ? `${seconds}s`
    : `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, '0')}s`;
  const nearlyOut = seconds >= TURN_CUTOFF_SECONDS - 60;
  return (
    <span
      className={`chat-elapsed${seconds >= TURN_IS_SLOW_SECONDS ? ' chat-elapsed--slow' : ''}`}
      data-testid="chat-elapsed"
    >
      {shown}
      {nearlyOut && ' — close to the 6 minute limit; past that the answer is lost'}
    </span>
  );
}

export function AgentChatPanel({
  agentId,
  agentName,
  onMessageSent,
  conversationId,
  initialMessages,
  onThreadChanged,
}: AgentChatPanelProps) {
  // Seeded on the FIRST render, not in an effect afterwards.
  //
  // Starting at `[]` meant the first commit reported an empty thread
  // to whoever owns the conversation -- the seeding effect had not run
  // yet, and the save effect reads the `messages` of the render it is
  // in. Opening any conversation that HAS messages therefore tried to
  // save nothing over it, which the store rightly refuses, and the
  // page showed "That message could not be saved." instead of the
  // thread. Found by opening a conversation the backend had just
  // written a turn into (2026-10-24).
  //
  // The effect below still resets on a conversation change; this only
  // removes the empty render that preceded it.
  const [messages, setMessages] = useState<ChatMessage[]>(() => initialMessages ?? []);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  // When the turn in flight began, for the elapsed counter. Null
  // whenever nothing is running, so the counter cannot show a
  // stale duration from a turn that already finished.
  const [turnStartedAt, setTurnStartedAt] = useState<number | null>(null);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [attachError, setAttachError] = useState<string | null>(null);
  // REQ-SB-82-US-06-T08 -- which earlier message (by its own `localId`)
  // the next Send should anchor as context. Purely in-memory for this
  // mount, never persisted (ADR-012 point 5).
  const [replyToLocalId, setReplyToLocalId] = useState<string | null>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const draftInputRef = useRef<HTMLTextAreaElement>(null);
  const nextLocalIdRef = useRef(0);

  function generateLocalId(): string {
    nextLocalIdRef.current += 1;
    return `msg-${nextLocalIdRef.current}`;
  }

  // Switching which agent this panel is pointed at (AgentDetailPanel
  // re-mounts a fresh instance per agentId via its own `key`, but
  // ChatPage's own single Primary-pointed instance never does) starts a
  // clean thread rather than carrying over a previous agent's messages.
  useEffect(() => {
    // Seeded from the stored thread when there is one, so switching
    // conversations shows the conversation rather than an empty panel. The
    // side panel passes none and still gets the clean slate it always had.
    setMessages(initialMessages ?? []);
    setDraft('');
    setSending(false);
    setTurnStartedAt(null);
    setAttachedFile(null);
    setAttachError(null);
    // Scenario 8 -- a reset that clears `messages` must also clear any
    // leftover `replyToLocalId` selection, or a stale reference could
    // survive into the fresh thread with nothing left to resolve it against.
    setReplyToLocalId(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (draftInputRef.current) draftInputRef.current.style.height = 'auto';
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `initialMessages` is the seed for THIS conversation, not a trigger: including it would reset the live thread every time the parent re-rendered.
  }, [agentId, conversationId]);

  // Persisted by whoever owns the conversation. Deliberately not on every
  // streamed frame: `isStreaming` bubbles are half a sentence, and saving each
  // one would write the file dozens of times per reply for no gain.
  useEffect(() => {
    if (!onThreadChanged || sending) return;
    onThreadChanged(messages);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- onThreadChanged is a fresh closure each parent render; keying off the thread itself avoids a save loop.
  }, [messages, sending]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, sending]);

  function handleFileSelect(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const extension = `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`;
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setAttachError(
        `'${extension}' files aren't supported yet — only PDF (.pdf), plain text (.txt), and Markdown (.md) files can be summarized today.`,
      );
      setAttachedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    setAttachError(null);
    setAttachedFile(file);
  }

  function handleRemoveAttachment() {
    setAttachedFile(null);
    setAttachError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  // 2026-08-24 -- pairs with the backend's own session-continuity fix:
  // a conversation now genuinely persists across messages (Hermes' own
  // gateway carries real history forward), so there needs to be an
  // explicit way to deliberately end one and start clean, same as a
  // real Hermes CLI session's own `/new` command.
  async function handleNewChat() {
    if (sending) return;
    setMessages([]);
    setDraft('');
    setAttachedFile(null);
    setAttachError(null);
    // Scenario 8 -- same reasoning as the agentId-switch reset above.
    setReplyToLocalId(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (draftInputRef.current) draftInputRef.current.style.height = 'auto';
    try {
      await resetChatSession(agentId);
    } catch {
      // The old session (if any) may already be dead server-side --
      // the thread is cleared either way, and the next real message
      // will open a fresh session on its own if this call itself failed.
    }
  }

  /** Answer the approval this agent is blocked on, and let the rest of
   *  the turn stream into a fresh bubble.
   *
   *  The answered bubble keeps its text and loses its buttons, so the
   *  thread still reads as what was asked and what was decided — and
   *  the decision cannot be made twice. */
  async function decideApproval(
    localId: string, choice: 'approve' | 'deny', always: boolean,
  ) {
    setMessages((prev) => prev.map((m) => (
      m.localId === localId ? { ...m, awaitingApproval: false } : m
    )));
    setSending(true);
    setTurnStartedAt(Date.now());
    const pendingId = generateLocalId();
    setMessages((prev) => [
      ...prev,
      { role: 'agent', text: '', activity: [], isStreaming: true, localId: pendingId },
    ]);
    const patch = (update: (message: ChatMessage) => ChatMessage) => {
      setMessages((prev) => prev.map((m) => (m.localId === pendingId ? update(m) : m)));
    };
    try {
      await answerChatApproval(agentId, choice, always, (streamEvent) => {
        if (streamEvent.type === 'approval') {
          // The agent asked for something ELSE straight after. Same
          // treatment: it is a decision, not a reply.
          patch((m) => ({
            ...m, text: streamEvent.text, isStreaming: false, awaitingApproval: true,
          }));
        } else if (streamEvent.type === 'activity') {
          patch((m) => ({ ...m, activity: [...(m.activity ?? []), streamEvent.text] }));
        } else if (streamEvent.type === 'delta') {
          patch((m) => ({ ...m, text: m.text + streamEvent.text }));
        } else if (streamEvent.type === 'complete') {
          patch((m) => ({ ...m, text: streamEvent.text || m.text, isStreaming: false }));
        } else if (streamEvent.type === 'error') {
          patch((m) => ({ ...m, text: streamEvent.detail, isStreaming: false, isError: true }));
        }
      }, conversationId);
    } catch {
      patch((m) => ({
        ...m,
        text: 'That decision could not be sent. The agent may have stopped waiting for it.',
        isStreaming: false,
        isError: true,
      }));
    } finally {
      setSending(false);
      setTurnStartedAt(null);
    }
  }

  async function handleSend(event: React.SyntheticEvent) {
    event.preventDefault();
    const text = draft.trim();
    if ((!text && !attachedFile) || sending) return;
    const bubbleText = attachedFile ? `${text} [attached: ${attachedFile.name}]`.trim() : text;
    // Resolved against the CURRENT `messages` array, before the new user
    // bubble below is appended to it. A `replyToLocalId` left over from a
    // reset that already cleared `messages` (Scenario 8) simply won't be
    // found here -- `replyToMessage` stays undefined and the send proceeds
    // as a plain, unanchored message, never a broken/blocked one.
    const replyToMessage = replyToLocalId
      ? messages.find((message) => message.localId === replyToLocalId)
      : undefined;
    setMessages((prev) => [...prev, { role: 'user', text: bubbleText, localId: generateLocalId() }]);
    setDraft('');
    if (draftInputRef.current) draftInputRef.current.style.height = 'auto';
    const fileToSend = attachedFile;
    setAttachedFile(null);
    setAttachError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    // Same "clear on send, regardless of outcome" pattern as `draft`/
    // `attachedFile` above.
    setReplyToLocalId(null);
    setSending(true);
    setTurnStartedAt(Date.now());
    // Context-anchoring mechanism (ADR-012 point 5): neither
    // `sendChatMessageWithAttachment` nor `streamChatMessage` accepts a
    // separate context parameter and no backend schema change is in
    // scope, so the referenced earlier message's own text is quoted
    // directly into the text actually sent to the agent. `bubbleText`
    // above (what renders in the thread) is built from the plain `text`
    // only -- the anchoring stays invisible plumbing, never a visible
    // echo in the user's own chat bubble.
    const outgoingText = replyToMessage ? `> ${replyToMessage.text}\n\n${text}` : text;
    try {
      if (fileToSend) {
        const response = await sendChatMessageWithAttachment(agentId, outgoingText, fileToSend);
        setMessages((prev) => [
          ...prev,
          {
            role: 'agent',
            text: response.reply,
            isError: response.attachment_status === 'rejected',
            localId: generateLocalId(),
          },
        ]);
      } else {
        // Streamed (2026-08-24) -- one pending bubble appended up front,
        // then filled in live by each real event frame rather than
        // waiting for the whole turn. `updatePendingMessage` always
        // targets the LAST message in the array: safe because this
        // bubble was JUST appended and nothing else appends a message
        // while `sending` is true (the composer/Send button are
        // disabled), so "last" and "this streaming reply" stay the same
        // message for the whole turn.
        setMessages((prev) => [
          ...prev,
          { role: 'agent', text: '', activity: [], isStreaming: true, localId: generateLocalId() },
        ]);
        function updatePendingMessage(update: (message: ChatMessage) => ChatMessage) {
          setMessages((prev) => {
            const next = [...prev];
            const lastIndex = next.length - 1;
            next[lastIndex] = update(next[lastIndex]);
            return next;
          });
        }
        function handleStreamEvent(streamEvent: ChatStreamEvent) {
          if (streamEvent.type === 'approval') {
            updatePendingMessage((m) => ({
              ...m,
              text: streamEvent.text,
              isStreaming: false,
              awaitingApproval: true,
            }));
          } else if (streamEvent.type === 'activity') {
            updatePendingMessage((m) => ({ ...m, activity: [...(m.activity ?? []), streamEvent.text] }));
          } else if (streamEvent.type === 'delta') {
            updatePendingMessage((m) => ({ ...m, text: m.text + streamEvent.text }));
          } else if (streamEvent.type === 'complete') {
            updatePendingMessage((m) => ({ ...m, text: streamEvent.text, isStreaming: false }));
          } else {
            updatePendingMessage((m) => ({
              ...m,
              text: m.text || 'Something went wrong sending that message. Please try again.',
              isError: true,
              isStreaming: false,
            }));
          }
        }
        // `conversationId` is passed so the BACKEND writes the turn
        // when the reply lands. Leaving this page mid-reply unmounts
        // the panel, and everything below this line stops happening —
        // including the save that used to be the only one.
        await streamChatMessage(
          agentId, outgoingText, handleStreamEvent, undefined, conversationId,
        );
      }
      onMessageSent?.();
    } catch {
      // A real Compass-backed reply can genuinely fail (network error,
      // Provider timeout) -- surfaced honestly in the thread itself, not
      // silently dropped, matching this project's own "honest, not
      // fabricated/swallowed" posture already established for actions.
      // The streamed path already appended its own pending bubble before
      // this could throw -- fill THAT one in rather than also appending
      // a second, stray error message alongside a forever-empty one.
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last?.role === 'agent' && last.isStreaming) {
          const next = [...prev];
          next[next.length - 1] = {
            ...last,
            text: last.text || 'Something went wrong sending that message. Please try again.',
            isError: true,
            isStreaming: false,
          };
          return next;
        }
        return [
          ...prev,
          {
            role: 'agent',
            text: 'Something went wrong sending that message. Please try again.',
            isError: true,
            localId: generateLocalId(),
          },
        ];
      });
    } finally {
      setSending(false);
      setTurnStartedAt(null);
    }
  }

  // Plain Enter sends (matches the old single-line <input>'s own native
  // form-submit-on-Enter behavior, so this isn't a regression); Shift+Enter
  // OR Alt+Enter inserts a real newline instead (operator, 2026-08-24: "when
  // I try to do a multiline text Alt+Enter Doesn't create a new line" --
  // Shift+Enter is the universal chat-app convention, Alt+Enter is
  // supported too as a direct alias for what was actually tried). A
  // <textarea> doesn't auto-submit its form on Enter the way a single
  // <input> does, so this handler is what makes plain Enter still send.
  function handleDraftKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.altKey) {
      event.preventDefault();
      handleSend(event);
      return;
    }
    // Tab inserts a real tab character at the cursor instead of moving
    // focus to the next control (operator: "include Bullets sometime with
    // Tab... a Default Text Editor") -- manual selection-range splice since
    // a controlled <textarea>'s value can't be mutated directly.
    if (event.key === 'Tab') {
      event.preventDefault();
      const target = event.currentTarget;
      const { selectionStart, selectionEnd } = target;
      const next = `${draft.slice(0, selectionStart)}\t${draft.slice(selectionEnd)}`;
      setDraft(next);
      requestAnimationFrame(() => {
        target.selectionStart = target.selectionEnd = selectionStart + 1;
      });
    }
  }

  // Auto-grows the textarea as real content wraps, from 3 lines up to a
  // real 5-line ceiling (operator: "need to grow bigger to show at least 3
  // to 5 lines") -- beyond that it scrolls internally rather than pushing
  // the rest of the panel around indefinitely.
  function handleDraftChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    setDraft(event.target.value);
    const el = event.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, _CHAT_INPUT_MAX_HEIGHT_PX)}px`;
  }

  function handleCancelReply() {
    setReplyToLocalId(null);
  }

  // Recomputed on every render from the live `messages` array, so a stale
  // `replyToLocalId` (Scenario 8) never renders a broken quote below.
  const resolvedReplyToMessage = replyToLocalId
    ? messages.find((message) => message.localId === replyToLocalId)
    : undefined;

  return (
    <div className="agent-chat-panel">
      {messages.length > 0 && (
        <div className="chat-panel-toolbar">
          <button type="button" className="chat-new-btn" onClick={handleNewChat} disabled={sending}>
            <span className="material-symbols-outlined" aria-hidden="true">add_comment</span>
            New chat
          </button>
        </div>
      )}
      <div className="chat-thread" data-role="agent-chat-thread">
        {messages.length === 0 && (
          <p className="text-muted chat-thread-empty">
            Ask {agentName} anything, or send one of its known trigger
            phrases to run an action directly.
          </p>
        )}
        {messages.map((message, index) => (
          <div
            className={`chat-message chat-message--${message.role}${message.isError ? ' chat-message--error' : ''}`}
            key={index}
          >
            {/* Real thinking/status trace (2026-08-24) -- collapsible,
                deliberately styled apart from the actual reply below it
                (operator: "displayed in italic much lighter color that
                the actual message to avoid chat being a mess") so it
                reads as ambient "still working" texture, never mistaken
                for the real answer. Auto-collapsed once real text starts
                landing; still expandable afterward via <details>'s own
                native disclosure, no extra state needed.

                Live summary shows the LATEST activity line itself, not a
                static "Working…" label (2026-08-30, operator: "the UI is
                telling Working I don't know WHich step its in... Agents
                should be Responsive with Which Agent it called and
                What's the current Status") -- now that tool.start/
                tool.complete frames actually reach here (agent_chat_
                stream.py), that latest line is real, useful text like
                `Calling terminal: hermes -p opp-manager chat -q "..."`,
                not a placeholder. */}
            {!!message.activity?.length && (
              <details className="chat-activity" open={message.isStreaming && !message.text}>
                <summary className={`chat-activity-summary${message.isStreaming ? ' chat-activity-summary--live' : ''}`}>
                  {message.isStreaming
                    ? message.activity[message.activity.length - 1]
                    : `Thought through ${message.activity.length} step${message.activity.length === 1 ? '' : 's'}`}
                  {/* How long it has been going (operator, 2026-10-24:
                      "it came back but it took very long time").
                      Measured on a real relay: Primary took 10s to
                      decide, then ADNOC Expert worked for 215s with a
                      single unchanging activity line on screen. The
                      line was true the whole time and told you nothing
                      about whether anything was still happening. */}
                  {message.isStreaming && <Elapsed since={turnStartedAt} />}
                </summary>
                {message.activity.map((line, activityIndex) => (
                  <p className="chat-activity-line" key={activityIndex}>{line}</p>
                ))}
              </details>
            )}
            {message.isStreaming && !message.text ? (
              <>
                <span className="chat-typing-dot" />
                <span className="chat-typing-dot" />
                <span className="chat-typing-dot" />
              </>
            ) : (
              <ChatMessageText text={message.text} />
            )}
            {/* The decision, on the bubble that asked for it. Hermes is
                holding the turn open on `approval.respond`; a typed
                reply goes in as a new prompt and answers nothing,
                which is what the operator hit. "Always" is Hermes' own
                `all` flag — approve this and everything like it for
                the rest of the session — and is not expressible as
                text at all. */}
            {message.awaitingApproval && (
              <div className="chat-approval" data-testid="chat-approval">
                <button
                  type="button"
                  className="btn"
                  disabled={sending}
                  onClick={() => void decideApproval(message.localId, 'approve', false)}
                >
                  Approve once
                </button>
                <button
                  type="button"
                  className="btn"
                  disabled={sending}
                  onClick={() => void decideApproval(message.localId, 'approve', true)}
                >
                  Always approve
                </button>
                <button
                  type="button"
                  className="btn btn-danger"
                  disabled={sending}
                  onClick={() => void decideApproval(message.localId, 'deny', false)}
                >
                  Decline
                </button>
              </div>
            )}
            {/* REQ-SB-82-US-06-T08 -- only a finalized bubble is
                repliable, never the still-live streaming placeholder
                above (its own `text` isn't settled yet to quote as
                context). Same user-facing verb/shape as Cockpit's own
                reply affordance (T07), built independently per
                ADR-012 point 5. */}
            {!message.isStreaming && (
              <button
                type="button"
                className="chat-message-reply-btn"
                aria-label="Reply to this message"
                onClick={() => setReplyToLocalId(message.localId)}
              >
                <span className="material-symbols-outlined" aria-hidden="true">reply</span>
              </button>
            )}
          </div>
        ))}
        {sending && !messages[messages.length - 1]?.isStreaming && (
          <div className="chat-message chat-message--agent chat-message--pending" aria-live="polite">
            <span className="chat-typing-dot" />
            <span className="chat-typing-dot" />
            <span className="chat-typing-dot" />
          </div>
        )}
        <div ref={threadEndRef} />
      </div>
      {attachError && (
        <p className="text-muted" data-role="chat-attach-error" role="alert">
          {attachError}
        </p>
      )}
      {attachedFile && (
        <div className="chat-attach-preview" data-role="chat-attach-preview">
          <span>📎 {attachedFile.name}</span>
          <button type="button" className="btn" onClick={handleRemoveAttachment}>
            Remove
          </button>
        </div>
      )}
      {/* REQ-SB-82-US-06-T08 -- Scenario 8: `resolvedReplyToMessage` is
          undefined whenever `replyToLocalId` no longer resolves against
          the CURRENT `messages` array (a stale reference), so this strip
          simply doesn't render rather than showing a broken/blank quote.
          `handleSend` independently re-resolves the same reference at
          send time, so Send always still works either way. */}
      {resolvedReplyToMessage && (
        <div className="chat-reply-to-preview" data-role="reply-to-preview">
          <span className="chat-reply-to-preview-text">
            ↳ Replying to: {truncateForReplyPreview(resolvedReplyToMessage.text)}
          </span>
          <button type="button" className="btn" aria-label="Cancel reply" onClick={handleCancelReply}>
            ×
          </button>
        </div>
      )}
      <form className="chat-input-row" onSubmit={handleSend}>
        {/* Icon button, not the raw file input (operator, 2026-08-24:
            "the Upload file Button in Chat to be an Icon to look
            better") -- the input itself stays in the DOM (real file
            picker behavior, screen-reader label) but visually hidden;
            this button just proxies a click onto it. */}
        <input
          type="file"
          accept=".pdf,.txt,.md"
          data-role="chat-attach-input"
          aria-label="Attach file"
          className="chat-attach-input-hidden"
          ref={fileInputRef}
          onChange={handleFileSelect}
          disabled={sending}
        />
        <button
          type="button"
          className="chat-attach-btn"
          aria-label="Attach a file"
          title="Attach a file"
          disabled={sending}
          onClick={() => fileInputRef.current?.click()}
        >
          <span className="material-symbols-outlined" aria-hidden="true">attach_file</span>
        </button>
        <textarea
          ref={draftInputRef}
          className="input chat-message-input"
          placeholder={`Message ${agentName}… (Shift+Enter for a new line)`}
          rows={3}
          value={draft}
          onChange={handleDraftChange}
          onKeyDown={handleDraftKeyDown}
          disabled={sending}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={sending || (!draft.trim() && !attachedFile)}
        >
          {sending ? 'Sending…' : 'Send'}
        </button>
      </form>
    </div>
  );
}
