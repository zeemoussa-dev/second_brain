import { AgentChatPanel } from '../features/chat/AgentChatPanel';

// New top-level Chat surface (2026-08-24, operator: "move the Primary
// Chat to be Background Agent, Create a new Tab we call Chat where we
// can Chat with this Agent Since it Talks to everything") -- Primary is
// now excluded from the Agents Map ring (agents_map_adapter.py's own
// `_BACKGROUND_AGENTS`), so this page is its real, primary way to be
// reached, not a second path alongside a map entry. "default" is
// Primary's own real agent id (hermes_definitions.py's own
// PRIMARY_PROFILE_ID convention), matching every other real call site
// in this codebase that addresses Primary directly.
export function ChatPage() {
  return (
    <div className="chat-page">
      <h1>Chat</h1>
      <p className="text-muted">
        Talk to Primary directly — the one agent that can see and act
        across everything, not just one narrow domain.
      </p>
      <div className="chat-page-panel">
        <AgentChatPanel agentId="default" agentName="Primary" />
      </div>
    </div>
  );
}
