import { useEffect, useRef, useState } from 'react';
import {
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
}

const ACCEPTED_EXTENSIONS = ['.pdf', '.txt', '.md'];
// ~5 lines at this input's own real font-size/line-height/padding
// (chat-message-input, agent-panel.css) -- the real ceiling
// handleDraftChange auto-grows up to before it starts scrolling
// internally instead of growing further.
const _CHAT_INPUT_MAX_HEIGHT_PX = 132;

interface AgentChatPanelProps {
  agentId: string;
  agentName: string;
  // AgentDetailPanel's own History tab needs to know a new turn just
  // landed so it can refresh; ChatPage has no History tab and omits
  // this entirely rather than being handed a no-op callback.
  onMessageSent?: () => void;
}

export function AgentChatPanel({ agentId, agentName, onMessageSent }: AgentChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [attachError, setAttachError] = useState<string | null>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const draftInputRef = useRef<HTMLTextAreaElement>(null);

  // Switching which agent this panel is pointed at (AgentDetailPanel
  // re-mounts a fresh instance per agentId via its own `key`, but
  // ChatPage's own single Primary-pointed instance never does) starts a
  // clean thread rather than carrying over a previous agent's messages.
  useEffect(() => {
    setMessages([]);
    setDraft('');
    setSending(false);
    setAttachedFile(null);
    setAttachError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (draftInputRef.current) draftInputRef.current.style.height = 'auto';
  }, [agentId]);

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

  async function handleSend(event: React.SyntheticEvent) {
    event.preventDefault();
    const text = draft.trim();
    if ((!text && !attachedFile) || sending) return;
    const bubbleText = attachedFile ? `${text} [attached: ${attachedFile.name}]`.trim() : text;
    setMessages((prev) => [...prev, { role: 'user', text: bubbleText }]);
    setDraft('');
    if (draftInputRef.current) draftInputRef.current.style.height = 'auto';
    const fileToSend = attachedFile;
    setAttachedFile(null);
    setAttachError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setSending(true);
    try {
      if (fileToSend) {
        const response = await sendChatMessageWithAttachment(agentId, text, fileToSend);
        setMessages((prev) => [
          ...prev,
          { role: 'agent', text: response.reply, isError: response.attachment_status === 'rejected' },
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
        setMessages((prev) => [...prev, { role: 'agent', text: '', activity: [], isStreaming: true }]);
        function updatePendingMessage(update: (message: ChatMessage) => ChatMessage) {
          setMessages((prev) => {
            const next = [...prev];
            const lastIndex = next.length - 1;
            next[lastIndex] = update(next[lastIndex]);
            return next;
          });
        }
        function handleStreamEvent(streamEvent: ChatStreamEvent) {
          if (streamEvent.type === 'activity') {
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
        await streamChatMessage(agentId, text, handleStreamEvent);
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
          { role: 'agent', text: 'Something went wrong sending that message. Please try again.', isError: true },
        ];
      });
    } finally {
      setSending(false);
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
