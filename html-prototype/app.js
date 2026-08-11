/*
  Second Brain prototype — shared interactive behaviour (REQ-SB-12, REQ-SB-13).
  No framework, no build step. Reused by every screen that needs the
  collapsible burger sidebar; agents-map.html additionally uses the agent
  detail panel and embedded-chat helpers.
*/

document.addEventListener('DOMContentLoaded', () => {
  // Collapsible burger-menu sidebar (REQ-SB-12).
  const toggle = document.getElementById('sidebarToggle');
  const shell = document.querySelector('.app-shell');
  if (toggle && shell) {
    toggle.addEventListener('click', () => {
      const collapsed = shell.classList.toggle('sidebar-collapsed');
      toggle.setAttribute('aria-expanded', String(!collapsed));
    });
  }

  // Buildable-state switcher: groups of [data-state-panel] toggled by
  // buttons carrying [data-state-target] inside the matching .state-switcher.
  document.querySelectorAll('.state-switcher').forEach((switcher) => {
    const group = switcher.dataset.group;
    const buttons = switcher.querySelectorAll('button[data-state-target]');
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        buttons.forEach((b) => b.classList.remove('btn-primary'));
        btn.classList.add('btn-primary');
        document
          .querySelectorAll(`[data-state-panel][data-group="${group}"]`)
          .forEach((panel) => {
            panel.classList.toggle('active', panel.dataset.state === btn.dataset.stateTarget);
          });
      });
    });
  });

  // Agents Map (REQ-SB-12) -> agent detail panel (REQ-SB-13).
  document.querySelectorAll('.agent-node').forEach((node) => {
    node.addEventListener('click', () => openAgentPanel(node.dataset.agentId));
  });
  const closeBtn = document.getElementById('agentPanelClose');
  if (closeBtn) closeBtn.addEventListener('click', closeAgentPanel);
  const overlay = document.getElementById('agentPanelOverlay');
  if (overlay) overlay.addEventListener('click', closeAgentPanel);

  // Embedded chat demo (REQ-SB-13): appends the user's message and a canned
  // agent reply so the reviewer can see the surface/motion, not real
  // inference — this prototype never calls a backend. Delegated (not
  // getElementById) because each agent's detail block repeats the same
  // chat markup, scoped by data-role rather than a page-unique id.
  document.addEventListener('submit', (event) => {
    const form = event.target.closest('[data-role="agent-chat-form"]');
    if (!form) return;
    event.preventDefault();
    const scope = form.closest('.side-panel-agent') || document;
    const input = scope.querySelector('[data-role="agent-chat-input"]');
    const thread = scope.querySelector('[data-role="agent-chat-thread"]');
    const text = input.value.trim();
    if (!text) return;
    appendChatMessage(thread, text, 'user');
    input.value = '';
    window.setTimeout(() => {
      appendChatMessage(thread, '(demo reply — this panel is a design prototype, not a live agent)', 'agent');
    }, 500);
  });
});

function openAgentPanel(agentId) {
  const panel = document.getElementById('agentPanel');
  const overlay = document.getElementById('agentPanelOverlay');
  if (!panel) return;
  document.querySelectorAll('[data-agent-detail]').forEach((el) => {
    el.classList.toggle('active', el.dataset.agentDetail === agentId);
  });
  panel.classList.add('open');
  if (overlay) overlay.classList.add('open');
}

function closeAgentPanel() {
  const panel = document.getElementById('agentPanel');
  const overlay = document.getElementById('agentPanelOverlay');
  if (panel) panel.classList.remove('open');
  if (overlay) overlay.classList.remove('open');
}

function appendChatMessage(thread, text, role) {
  if (!thread) return;
  const el = document.createElement('div');
  el.className = `chat-message chat-message--${role}`;
  el.textContent = text;
  thread.appendChild(el);
  thread.scrollTop = thread.scrollHeight;
}
